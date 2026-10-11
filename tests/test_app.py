from pathlib import Path
from streamlit.testing.v1 import AppTest
from utils.data_processing import load_upload


def test_empty_app():
    app = AppTest.from_file(Path("app.py").resolve()).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Campaign Advisor"


def test_all_tabs_with_real_workbook():
    path = Path("GenAcademy_week1_Outreach.xlsx")
    data = load_upload(path.read_bytes(), path.name)
    script = """
import streamlit as st
from components import overview, outreach, responses, bulk_closure
for component in [overview, outreach, responses, bulk_closure]:
    component.render(st.session_state['dataset'])
"""
    app = AppTest.from_string(script)
    app.session_state["dataset"] = data
    app.run(timeout=30)
    assert not app.exception
    assert len(app.selectbox) == 11
    app.selectbox[1].select("Dental").run()
    assert not app.exception
