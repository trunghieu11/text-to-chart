"""
Admin UI - Operator UI for managing tenants, keys, usage.

Run with: streamlit run admin_ui/app.py --server.port 5003

Requires ADMIN_USERNAME and ADMIN_PASSWORD in env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config  # noqa: F401
import streamlit as st

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api_get(path: str, admin_user: str, admin_pass: str) -> tuple[int, dict]:
    import urllib.request
    import json as _json
    import base64

    auth = base64.b64encode(f"{admin_user}:{admin_pass}".encode()).decode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Basic {auth}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, _json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, _json.loads(body)
        except Exception:
            return e.code, {"detail": body}


def _api_post(
    path: str, json: dict, admin_user: str, admin_pass: str
) -> tuple[int, dict]:
    import urllib.request
    import json as _json
    import base64

    auth = base64.b64encode(f"{admin_user}:{admin_pass}".encode()).decode()
    data = _json.dumps(json).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, _json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, _json.loads(body)
        except Exception:
            return e.code, {"detail": body}


def _api_patch(
    path: str, json: dict, admin_user: str, admin_pass: str
) -> tuple[int, dict]:
    import urllib.request
    import json as _json
    import base64

    auth = base64.b64encode(f"{admin_user}:{admin_pass}".encode()).decode()
    data = _json.dumps(json).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, _json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, _json.loads(body)
        except Exception:
            return e.code, {"detail": body}


def _api_delete(path: str, admin_user: str, admin_pass: str) -> int:
    import urllib.request
    import base64

    auth = base64.b64encode(f"{admin_user}:{admin_pass}".encode()).decode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Basic {auth}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req):
            return 200
    except urllib.error.HTTPError as e:
        return e.code


def main():
    st.set_page_config(page_title="Admin UI", page_icon="⚙️", layout="wide")

    admin_user = config.config.admin_username
    admin_pass = config.config.admin_password

    if not admin_user or not admin_pass:
        st.error("ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment.")
        st.code("export ADMIN_USERNAME=admin\nexport ADMIN_PASSWORD=your-secret")
        return

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u == admin_user and p == admin_pass:
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = u
                    st.session_state.admin_pass = p
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return

    u = st.session_state.admin_user
    p = st.session_state.admin_pass

    st.title("Admin UI")
    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

    status, data = _api_get("/admin/v1/tenants", u, p)
    if status != 200:
        st.error(data.get("detail", "Failed to load tenants"))
        return

    tenants = data.get("tenants", [])
    if not tenants:
        st.info("No tenants yet.")
        return

    search = st.text_input("Search tenants", placeholder="Filter by name or email...")
    if search:
        search_lower = search.lower()
        tenants = [
            t
            for t in tenants
            if search_lower in (t.get("name", "") or "").lower()
            or search_lower in (t.get("email", "") or "").lower()
        ]

    for t in tenants:
        with st.expander(f"{t.get('name', '')} ({t.get('email', '')}) - {t.get('plan_name', '')} - {t.get('status', '')}"):
            tenant_id = t["id"]

            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox(
                    "Status",
                    ["active", "suspended"],
                    index=0 if t.get("status") == "active" else 1,
                    key=f"status_{tenant_id}",
                )
                if st.button("Update status", key=f"upd_status_{tenant_id}"):
                    code, _ = _api_patch(
                        f"/admin/v1/tenants/{tenant_id}",
                        {"status": new_status},
                        u,
                        p,
                    )
                    if code == 200:
                        st.success("Updated")
                        st.rerun()
                    else:
                        st.error("Failed")

            with col2:
                st.caption("Change plan (1=free, 2=pro, 3=enterprise)")
                plan_id = st.number_input(
                    "Plan ID",
                    min_value=1,
                    max_value=3,
                    value=t.get("plan_id", 1),
                    key=f"plan_{tenant_id}",
                )
                if st.button("Update plan", key=f"upd_plan_{tenant_id}"):
                    code, _ = _api_patch(
                        f"/admin/v1/tenants/{tenant_id}",
                        {"plan_id": plan_id},
                        u,
                        p,
                    )
                    if code == 200:
                        st.success("Updated")
                        st.rerun()
                    else:
                        st.error("Failed")

            st.subheader("Keys")
            status2, keys_data = _api_get(f"/admin/v1/tenants/{tenant_id}/keys", u, p)
            if status2 == 200:
                keys = keys_data.get("keys", [])
                for k in keys:
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.text(f"{k['name']} - {k['key_prefix']}...")
                    with c2:
                        st.caption(k["created_at"])
                    with c3:
                        if st.button("Revoke", key=f"revoke_{tenant_id}_{k['id']}"):
                            _api_delete(
                                f"/admin/v1/tenants/{tenant_id}/keys/{k['id']}",
                                u,
                                p,
                            )
                            st.rerun()

                with st.form(f"create_key_{tenant_id}"):
                    key_name = st.text_input("New key name", value="Default")
                    if st.form_submit_button("Create key"):
                        code, kdata = _api_post(
                            f"/admin/v1/tenants/{tenant_id}/keys",
                            {"name": key_name},
                            u,
                            p,
                        )
                        if code == 200:
                            st.success("Key created (copy now):")
                            st.code(kdata.get("key", ""))
                            st.rerun()
                        else:
                            st.error(kdata.get("detail", "Failed"))
            else:
                st.error("Failed to load keys")

            st.subheader("Usage")
            status3, usage_data = _api_get(
                f"/admin/v1/tenants/{tenant_id}/usage", u, p
            )
            if status3 == 200:
                curr = usage_data.get("current", {})
                st.metric("This month", curr.get("request_count", 0))
                hist = usage_data.get("history", [])
                if hist:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(hist), use_container_width=True, hide_index=True)
            else:
                st.error("Failed to load usage")


if __name__ == "__main__":
    main()
