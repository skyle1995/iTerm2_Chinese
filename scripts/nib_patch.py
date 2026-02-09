#!/usr/bin/env python3
"""
NIBArchive patcher: parse nib using nibarchive library, modify strings,
serialize back to binary.
"""

import struct
import sys
import io
import json

sys.path.insert(0, '/tmp/nibenv/lib/python3.12/site-packages')
from nibarchive import NIBArchiveParser, NIBValueType, NIBArchive, NIBValue


def encode_varint(value):
    """Encode varint using NIBArchive convention (high bit = last byte)."""
    if value < 0x80:
        return bytes([value | 0x80])

    result = bytearray()
    while value > 0:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            byte |= 0x80  # mark last byte
        result.append(byte)
    return bytes(result)


def serialize_nib(nib: NIBArchive) -> bytes:
    """Serialize a NIBArchive back to binary format."""

    # Build objects section
    objects_buf = bytearray()
    for obj in nib.objects:
        objects_buf += encode_varint(obj.class_name_index)
        objects_buf += encode_varint(obj.values_index)
        objects_buf += encode_varint(obj.value_count)

    # Build keys section
    keys_buf = bytearray()
    for key in nib.keys:
        key_bytes = key.name.encode('utf-8')
        keys_buf += encode_varint(len(key_bytes))
        keys_buf += key_bytes

    # Build values section
    values_buf = bytearray()
    for val in nib.values:
        values_buf += encode_varint(val.key_index)

        vtype = val.type
        if vtype == NIBValueType.NIBARCHIVE:
            # Nested nib - serialize recursively
            vtype = NIBValueType.DATA
            nested_data = serialize_nib(val.data)
            values_buf += bytes([vtype.value])
            values_buf += encode_varint(len(nested_data))
            values_buf += nested_data
            continue

        values_buf += bytes([vtype.value])

        if vtype == NIBValueType.INT8:
            values_buf += bytes([val.data & 0xFF])
        elif vtype == NIBValueType.INT16:
            values_buf += struct.pack('<h', val.data)
        elif vtype == NIBValueType.INT32:
            values_buf += struct.pack('<i', val.data)
        elif vtype == NIBValueType.INT64:
            values_buf += struct.pack('<q', val.data)
        elif vtype == NIBValueType.BOOL_TRUE:
            pass  # no data
        elif vtype == NIBValueType.BOOL_FALSE:
            pass  # no data
        elif vtype == NIBValueType.FLOAT:
            values_buf += struct.pack('<f', val.data)
        elif vtype == NIBValueType.DOUBLE:
            values_buf += struct.pack('<d', val.data)
        elif vtype == NIBValueType.DATA:
            if isinstance(val.data, bytes):
                values_buf += encode_varint(len(val.data))
                values_buf += val.data
            elif isinstance(val.data, list):
                # Packed doubles with 0x07 prefix
                if len(val.data) == 2:
                    packed = bytes([0x07]) + struct.pack('<dd', *val.data)
                elif len(val.data) == 4:
                    packed = bytes([0x07]) + struct.pack('<dddd', *val.data)
                else:
                    packed = bytes(val.data)
                values_buf += encode_varint(len(packed))
                values_buf += packed
            else:
                values_buf += encode_varint(0)
        elif vtype == NIBValueType.NIL:
            pass  # no data
        elif vtype == NIBValueType.OBJECT_REF:
            values_buf += struct.pack('<i', val.data)

    # Build class names section
    classnames_buf = bytearray()
    for cn in nib.class_names:
        name_bytes = cn.name.encode('utf-8') + b'\x00'
        classnames_buf += encode_varint(len(name_bytes))
        classnames_buf += encode_varint(cn.extras_count)
        classnames_buf += struct.pack('<%s' % ('i' * cn.extras_count), *cn.extras)
        classnames_buf += name_bytes

    # Calculate offsets
    header_size = 50  # 10 magic + 40 header bytes
    offset_objects = header_size
    offset_keys = offset_objects + len(objects_buf)
    offset_values = offset_keys + len(keys_buf)
    offset_classnames = offset_values + len(values_buf)

    # Build header
    header = bytearray()
    header += b'NIBArchive'
    header += struct.pack('<iiiiiiiiii',
        nib.header.unknown_1,
        nib.header.unknown_2,
        len(nib.objects), offset_objects,
        len(nib.keys), offset_keys,
        len(nib.values), offset_values,
        len(nib.class_names), offset_classnames,
    )

    return bytes(header) + bytes(objects_buf) + bytes(keys_buf) + bytes(values_buf) + bytes(classnames_buf)


def patch_nib(nib_path, translations, output_path):
    """
    Patch a .nib file with translated strings.
    translations: {"obj_idx.key_name": "translated string"}
    """
    parser = NIBArchiveParser()
    with open(nib_path, 'rb') as f:
        nib = parser.parse(f)

    # Build lookup
    trans_lookup = {}
    for k, v in translations.items():
        parts = k.split('.', 1)
        obj_idx = int(parts[0])
        key_name = parts[1]
        trans_lookup[(obj_idx, key_name)] = v

    # Apply translations
    patched = 0
    for obj_idx, obj in enumerate(nib.objects):
        for val in nib.get_object_values(obj):
            key_name = nib.keys[val.key_index].name
            lookup_key = (obj_idx, key_name)

            if lookup_key in trans_lookup and val.type == NIBValueType.DATA:
                if isinstance(val.data, bytes):
                    new_text = trans_lookup[lookup_key]
                    val.data = new_text.encode('utf-8') + b'\x00'
                    patched += 1

    # Serialize
    output = serialize_nib(nib)

    with open(output_path, 'wb') as f:
        f.write(output)

    return patched


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <original.nib> <translations.json> <output.nib>")
        sys.exit(1)

    nib_path = sys.argv[1]
    trans_path = sys.argv[2]
    output_path = sys.argv[3]

    with open(trans_path) as f:
        translations = json.load(f)

    count = patch_nib(nib_path, translations, output_path)
    print(f"Patched {count} strings -> {output_path}")


if __name__ == '__main__':
    main()
