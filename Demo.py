from PBDecoder import decodeProto, ProtobufDisplay
from PBEncoder import encodeProto

if __name__ == '__main__':
    ProtoBuf = bytes.fromhex("08C45E1218E5B7B2E59CA8E585B6E4BB96E59CB0E696B9E799BBE5BD95")
    result = decodeProto(ProtoBuf)
    Data = ProtobufDisplay(result, True)  # 如果需要转回ProtoBuf参数2为True，会输出value类型。
    print(Data)

    ProtoBuf = encodeProto(Data).hex()
    print(ProtoBuf)
