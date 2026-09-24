#!/usr/bin/env python3
"""验收:提交够线/不够线各一笔,总表都要按新编号可见,且无"待同步"提示。

先启动服务(docker compose up),再运行:

    python3 tests/acceptance_test.py

环境变量 BASE_URL 可覆盖入口地址,默认 http://localhost:3192。
仅用标准库,退出码非 0 即验收失败。
"""
import http.cookiejar
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:3192").rstrip("/")
RUN = str(os.getpid())

failures = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def opener_for(user, password):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(
        BASE + "/login",
        data=urllib.parse.urlencode({"username": user, "password": password}).encode(),
    )
    op.open(req)
    return op


def get(op, path):
    return op.open(BASE + path).read().decode()


def post_cupping(op, lot, aroma, taste, liquor):
    """按页面表单的方式提交(HX 局部刷新),返回服务端给出的新行 HTML。"""
    req = urllib.request.Request(
        BASE + "/cuppings",
        data=urllib.parse.urlencode(
            {"lot": lot, "aroma": aroma, "taste": taste, "liquor": liquor}
        ).encode(),
        headers={"HX-Request": "true"},
    )
    return op.open(req).read().decode()


def row_ids(html):
    return [int(m) for m in re.findall(r'data-id="(\d+)"', html)]


def main():
    # 服务存活
    try:
        urllib.request.urlopen(BASE + "/health", timeout=5)
    except Exception as exc:
        print(f"服务不可达 {BASE}: {exc}")
        return 2

    taster = opener_for("taster", "tea123456")

    home0 = get(taster, "/")
    check("提交前总表无“待同步”提示", "待同步" not in home0)
    ids_before = row_ids(home0)

    # 够线一笔:8/8/8 -> 8.0 通过
    lot_pass = f"验收-够线-{RUN}"
    row_html = post_cupping(taster, lot_pass, 8, 8, 8)
    ids_new = row_ids(row_html)
    check("够线提交返回的新行带编号", len(ids_new) == 1, row_html[:120])
    id_pass = ids_new[0] if ids_new else None

    # 不够线一笔:4/4/4 -> 4.0 不通过
    lot_fail = f"验收-不够线-{RUN}"
    row_html = post_cupping(taster, lot_fail, 4, 4, 4)
    ids_new = row_ids(row_html)
    check("不够线提交返回的新行带编号", len(ids_new) == 1, row_html[:120])
    id_fail = ids_new[0] if ids_new else None

    home1 = get(taster, "/")
    ids_after = row_ids(home1)

    check("总表含够线新编号", id_pass in ids_after, f"ids={ids_after}")
    check("总表含不够线新编号", id_fail in ids_after, f"ids={ids_after}")
    check("总表含够线批次名", lot_pass in home1)
    check("总表含不够线批次名", lot_fail in home1)
    check(
        "新行在表头(最新两笔居前,原有顺序不变)",
        ids_after[:2] == [id_fail, id_pass] and ids_after[2:] == ids_before,
        f"after={ids_after} before={ids_before}",
    )
    check("提交后总表无“待同步”提示", "待同步" not in home1)

    # 回归:observer 只看,没有提交表单
    observer = opener_for("observer", "look123456")
    obs = get(observer, "/")
    check("observer 总表同样含两笔新编号", id_pass in row_ids(obs) and id_fail in row_ids(obs))
    check("observer 无提交表单", 'action="/cuppings"' not in obs)
    check("observer 页面无“待同步”提示", "待同步" not in obs)

    print()
    if failures:
        print(f"验收失败 {len(failures)} 项:")
        for f in failures:
            print(" - " + f)
        return 1
    print("全部验收通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
