import argparse
from core import fangxss, fangsql, fanglfi, fangrce

def main():
    parser = argparse.ArgumentParser(description="BloodFANG Offensive Toolkit")
    parser.add_argument("--xss", help="Target URL for XSS scan")
    parser.add_argument("--sql", help="Target URL for SQLi scan")
    parser.add_argument("--lfi", help="Target URL for LFI scan")
    parser.add_argument("--rce", help="Target URL for RCE scan")
    parser.add_argument("--param", help="Parameter to test", default="q")
    args = parser.parse_args()

    if args.xss:
        fangxss.scan_xss(args.xss, args.param)
    if args.sql:
        fangsql.scan_sqli(args.sql, args.param)
    if args.lfi:
        fanglfi.scan_lfi(args.lfi, args.param)
    if args.rce:
        fangrce.scan_rce(args.rce, args.param)

if __name__ == "__main__":
    main()

