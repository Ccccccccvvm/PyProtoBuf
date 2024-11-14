import struct




def encodeProto(data):
    def encode_varint(value):
        """Encode an integer as a varint."""
        buf = b''
        while value > 0x7f:
            buf += bytes([(value & 0x7f) | 0x80])
            value >>= 7
        buf += bytes([value])
        return buf

    def encode_length_delimited(value):
        """Encode a length-delimited field."""
        if isinstance(value, str):
            value = value.encode()
        length_bytes = encode_varint(len(value))
        return length_bytes + value

    def encode_field(index, value, wire_type):
        """Encode a single field."""
        # Combine index and wire type
        tag = (index << 3) | wire_type
        tag_bytes = encode_varint(tag)

        if wire_type == 0:  # VARINT
            return tag_bytes + encode_varint(value)
        elif wire_type == 2:  # LENGTH_DELIMITED
            return tag_bytes + encode_length_delimited(value)
        elif wire_type == 1:  # FIXED64
            return tag_bytes + struct.pack('<Q', value)
        elif wire_type == 5:  # FIXED32

            return tag_bytes + struct.pack('<I', value)
        else:
            raise ValueError(f"Unsupported wire type: {wire_type}")

    def encode_nested_dict(nested_dict):
        """Recursively encode a nested dictionary."""
        encoded = b''
        for index, value in nested_dict.items():
            if isinstance(value, tuple):
                # Simple type
                wire_type, val = value
                encoded += encode_field(index, val, wire_type)
            elif isinstance(value, dict):
                # Nested message
                nested_encoded = encode_nested_dict(value)
                encoded += encode_field(index, nested_encoded, 2)
            elif isinstance(value, list):
                # Repeated field
                for item in value:
                    if isinstance(item, tuple):
                        wire_type, val = item
                        encoded += encode_field(index, val, wire_type)
                    elif isinstance(item, dict):
                        nested_encoded = encode_nested_dict(item)
                        encoded += encode_field(index, nested_encoded, 2)
        return encoded

    return encode_nested_dict(data)
