#!/usr/bin/env python3

from cryptography import x509
from cryptography.hazmat.backends import default_backend
import hashlib
import os
import sys
import argparse
import struct

def format_name(name):
    """格式化 x509.Name 对象为可读字符串"""
    return ", ".join([f"{attr.oid._name}={attr.value}" for attr in name])

def calculate_openssl_subject_hash_old(cert_data):
    """
    模仿 OpenSSL 'subject_hash_old'
    
    Args:
        cert_data: 证书的二进制数据
    
    Returns:
        str: 8字符的十六进制哈希值
    """
    try:
        # 尝试 PEM 格式
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    except ValueError:
        try:
            # 尝试 DER 格式
            cert = x509.load_der_x509_certificate(cert_data, default_backend())
        except ValueError as e:
            raise ValueError(f"无法解析证书: {e}")
    
    # 获取主题名称的 DER 编码
    subject_der = cert.subject.public_bytes()
    
    # 计算 MD5 哈希（二进制形式）
    md5_bytes = hashlib.md5(subject_der).digest()
    
    # 使用小端序解释前4个字节
    # 这与 OpenSSL 的 subject_hash_old 完全一致
    openssl_hash = struct.unpack('<I', md5_bytes[:4])[0]  # 小端序无符号整数
    openssl_hash = f"{openssl_hash:08x}"  # 格式化为8位十六进制
    
    return openssl_hash

def process_certificate_file(cert_path, output_dir=None, android_format=False):
    """
    处理证书文件并计算哈希值
    
    Args:
        cert_path: 证书文件路径
        output_dir: 输出目录（可选）
        android_format: 是否生成 Android 格式文件
    
    Returns:
        dict: 包含证书信息的字典
    """
    print(f"处理证书: {cert_path}")
    print("=" * 50)
    
    # 读取证书文件
    with open(cert_path, 'rb') as f:
        cert_data = f.read()
    
    # 计算哈希值
    hash_value = calculate_openssl_subject_hash_old(cert_data)
    
    # 解析证书获取详细信息
    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        cert_format = "PEM"
    except ValueError:
        cert = x509.load_der_x509_certificate(cert_data, default_backend())
        cert_format = "DER"
    
    # 使用 UTC 时间
    not_valid_before = cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S")
    not_valid_after = cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S")
    
    # 提取证书信息
    cert_info = {
        'file_path': cert_path,
        'hash_value': hash_value,
        'format': cert_format,
        'subject': format_name(cert.subject),
        'issuer': format_name(cert.issuer),
        'serial_number': str(cert.serial_number),
        'not_valid_before': not_valid_before,
        'not_valid_after': not_valid_after,
        'signature_algorithm': cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else 'Unknown'
    }
    
    # 显示结果
    print(f"证书哈希 (subject_hash_old): {hash_value}")
    print(f"证书格式: {cert_format}")
    print(f"证书主题: {cert_info['subject']}")
    print(f"颁发者: {cert_info['issuer']}")
    print(f"序列号: {cert_info['serial_number']}")
    print(f"有效期: {cert_info['not_valid_before']} 至 {cert_info['not_valid_after']}")
    print(f"签名算法: {cert_info['signature_algorithm']}")
    
    # 生成输出文件
    if output_dir or android_format:
        if not output_dir:
            output_dir = os.path.dirname(cert_path) or '.'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Android 格式: {hash}.0
        if android_format:
            android_filename = f"{hash_value}.0"
            android_path = os.path.join(output_dir, android_filename)
            
            with open(android_path, 'wb') as f:
                f.write(cert_data)
            
            print(f"Android 格式文件已生成: {android_path}")
            cert_info['android_file'] = android_path
    
    print()
    return cert_info

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='计算 X509 证书的 subject_hash_old 哈希值')
    parser.add_argument('cert_path', nargs='?', help='证书文件路径或包含证书的目录路径')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-a', '--android', action='store_true', 
                       help='生成 Android 系统格式的文件 ({hash}.0)')
    
    args = parser.parse_args()
    
    # 如果没有提供证书路径，检查默认文件
    if not args.cert_path:
        cert_file = "mitmproxy-ca-cert.cer"
        if os.path.exists(cert_file):
            print("检测到 mitmproxy-ca-cert.cer，正在计算哈希值...\n")
            process_certificate_file(cert_file, args.output, args.android)
            return 0
        else:
            print("错误: 未提供证书路径且未找到默认文件 mitmproxy-ca-cert.cer")
            print("\n使用方法:")
            print("  python hash.py <证书文件或目录> [选项]")
            print("\n选项:")
            print("  -o, --output DIR   输出目录")
            print("  -a, --android      生成 Android 格式文件")
            print("\n示例:")
            print("  python hash.py mitmproxy-ca-cert.cer")
            print("  python hash.py mitmproxy-ca-cert.cer -a")
            print("  python hash.py /path/to/certs -a -o ./output")
            return 1
    
    if not os.path.exists(args.cert_path):
        print(f"错误: 路径 {args.cert_path} 不存在")
        return 1
    
    try:
        if os.path.isdir(args.cert_path):
            # 批量处理目录
            print(f"批量处理目录: {args.cert_path}")
            cert_extensions = ('.cer', '.pem', '.crt', '.der')
            cert_files = [f for f in os.listdir(args.cert_path) 
                         if f.lower().endswith(cert_extensions)]
            
            if not cert_files:
                print(f"在 {args.cert_path} 中未找到证书文件")
                return 1
                
            results = []
            for cert_file in cert_files:
                cert_path = os.path.join(args.cert_path, cert_file)
                try:
                    cert_info = process_certificate_file(cert_path, args.output, args.android)
                    results.append(cert_info)
                except Exception as e:
                    print(f"处理 {cert_file} 时出错: {e}")
                    print()
            
            if results:
                print(f"成功处理 {len(results)} 个证书文件")
                print("\n汇总:")
                for cert_info in results:
                    print(f"  {os.path.basename(cert_info['file_path'])}: {cert_info['hash_value']}")
        else:
            # 处理单个文件
            process_certificate_file(args.cert_path, args.output, args.android)
        
        return 0
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
