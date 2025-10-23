# simple_suite_tool.py
import sys
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import msgpack

# Fill these two thing first with format like: b'put_string_here' 
AES_KEY = b'THE_KEY'
AES_IV = b'THE_IV'

def decrypt_suite(input_file, output_json):
    """解密suite文件到JSON"""
    with open(input_file, 'rb') as f:
        encrypted = f.read()
    
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=AES_IV)
    decrypted = unpad(cipher.decrypt(encrypted), 16)
    
    # 兼容不同版本的msgpack
    try:
        data = msgpack.unpackb(decrypted, strict_map_key=False)
    except TypeError:
        # 如果strict_map_key参数不被支持，使用默认方式
        data = msgpack.unpackb(decrypted)
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"解密完成: {input_file} -> {output_json}")

def encrypt_suite(input_json, output_file):
    """加密JSON文件到suite格式"""
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 兼容不同版本的msgpack
    try:
        packed = msgpack.packb(data, strict_map_key=False)
    except TypeError:
        # 如果strict_map_key参数不被支持，使用默认方式
        packed = msgpack.packb(data)
    
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=AES_IV)
    encrypted = cipher.encrypt(pad(packed, 16))
    
    with open(output_file, 'wb') as f:
        f.write(encrypted)
    
    print(f"加密完成: {input_json} -> {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法:")
        print("  解密: python simple_suite_tool.py decrypt input.suite output.json")
        print("  加密: python simple_suite_tool.py encrypt input.json output.suite")
        sys.exit(1)
    
    command, input_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
    
    if command == "decrypt":
        decrypt_suite(input_path, output_path)
    elif command == "encrypt":
        encrypt_suite(input_path, output_path)
    else:
        print("未知命令，使用 'decrypt' 或 'encrypt'")
