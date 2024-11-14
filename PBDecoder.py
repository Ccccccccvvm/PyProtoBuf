import struct


class BufferReader:
    def __init__(self, buffer):
        self.buffer = buffer
        self.offset = 0

    def read_varint(self):
        value, length = self.decode_varint(self.buffer, self.offset)
        self.offset += length
        return value

    def read_buffer(self, length):
        self.check_byte(length)
        result = self.buffer[self.offset:self.offset + length]
        self.offset += length
        return result

    def try_skip_grpc_header(self):
        backup_offset = self.offset

        # 首先检查缓冲区是否为空
        if not self.buffer:
            return

        # 检查是否有足够的字节
        if self.left_bytes() >= 5 and self.buffer[self.offset] == 0:
            self.offset += 1

            # 确保有足够的字节读取 4 字节的长度
            if self.left_bytes() >= 4:
                length = struct.unpack('>I', self.buffer[self.offset:self.offset + 4])[0]
                self.offset += 4

                # 检查长度是否合法
                if length <= self.left_bytes():
                    return

        # 如果任何检查失败，恢复到原始偏移量
        self.offset = backup_offset

    def left_bytes(self):
        return len(self.buffer) - self.offset

    def check_byte(self, length):
        bytes_available = self.left_bytes()
        if length > bytes_available:
            raise ValueError(f"Not enough bytes left. Requested: {length} left: {bytes_available}")

    def checkpoint(self):
        self.saved_offset = self.offset

    def reset_to_checkpoint(self):
        self.offset = self.saved_offset

    def decode_varint(self, buffer, offset):
        value = 0
        shift = 0
        length = 0

        while True:
            byte = buffer[offset]
            offset += 1
            value |= (byte & 0x7F) << shift
            length += 1
            if byte & 0x80 == 0:
                break
            shift += 7

        return value, length


TYPES = {
    'VARINT': 0,
    'FIXED64': 1,
    'LENDELIM': 2,
    'FIXED32': 5
}


def decodeProto(buffer):
    reader = BufferReader(buffer)
    parts = []

    reader.try_skip_grpc_header()

    try:
        while reader.left_bytes() > 0:
            reader.checkpoint()

            byte_range = [reader.offset]
            index_type = reader.read_varint()
            type_ = index_type & 0b111
            index = index_type >> 3

            if type_ == TYPES['VARINT']:
                value = reader.read_varint()
            elif type_ == TYPES['LENDELIM']:
                length = reader.read_varint()
                value = reader.read_buffer(length)
            elif type_ == TYPES['FIXED32']:

                value = reader.read_buffer(4)
            elif type_ == TYPES['FIXED64']:
                value = reader.read_buffer(8)
            else:
                raise ValueError(f"Unknown type: {type_}")

            byte_range.append(reader.offset)

            parts.append({
                'byteRange': byte_range,
                'index': index,
                'type': type_,
                'value': value
            })
    except Exception as err:
        reader.reset_to_checkpoint()

    return {
        'parts': parts,
        'leftOver': reader.read_buffer(reader.left_bytes())
    }


def type_to_string(type_, sub_type=None):
    if type_ == TYPES['VARINT']:
        return "varint"
    elif type_ == TYPES['LENDELIM']:
        return sub_type or "len_delim"
    elif type_ == TYPES['FIXED32']:
        return "fixed32"
    elif type_ == TYPES['FIXED64']:
        return "fixed64"
    else:
        return "unknown"


def decoded_to_dict(decoded, IsType=True):
    result = {}
    # for part in decoded["parts"]:
    #     index = part["index"]
    #     value = getProtobufPart(part, IsType)
    #     result[index] = value
    for part in decoded["parts"]:
        index = part["index"]
        value = getProtobufPart(part, IsType)
        if index not in result:
            result[index] = value
        else:
            if isinstance(result[index], list):
                result[index].append(value)
            else:
                result[index] = [result[index], value]

    return result


def getProtobufPart(part, IsType=True):
    part_type = part["type"]
    part_value = part["value"]
    if part_type == TYPES["VARINT"]:
        if IsType:
            return part_type, part_value
        return part_value

    elif part_type == TYPES["LENDELIM"]:
        decoded = decodeProto(part_value)

        if len(part_value) > 0 and len(decoded["leftOver"]) == 0:
            return decoded_to_dict(decoded,IsType)
        else:
            if IsType:
                return part_type, part_value.decode("utf-8")
            return part_value.decode("utf-8")
    elif part_type == TYPES["FIXED64"]:
        part_value = struct.unpack('<Q', part_value)[0]
        if IsType:
            return part_type, part_value
        return part_value

    elif part_type == TYPES["FIXED32"]:
        part_value = struct.unpack('<I', part_value)[0]
        if IsType:
            return part_type, part_value
        return part_value

    else:
        raise Exception(f"Unknown type {part_type}")


def ProtobufPart(part, IsType=True):
    return getProtobufPart(part, IsType)


def ProtobufDisplay(part,IsType=True):
    result = {}

    for k in part["parts"]:
        Part = ProtobufPart(k,IsType )
        k["index"]
        if k["index"] not in result:
            result[k["index"]] = Part
        else:
            if isinstance(result[k["index"]], list):
                result[k["index"]].append(Part)
            else:
                result[k["index"]] = [result[k["index"]], Part]
    return result

