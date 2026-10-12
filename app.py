"""Streamlit UI: python -m streamlit run app.py"""

import os
import tempfile

import streamlit as st

from backend.musicxml_generator import write_musicxml
from backend.wav_generator import write_wav
from compiler.compiler import compile_file
from compiler.ir import format_ir
from utils.errors import LexicalError, ParserError, SemanticError

st.set_page_config(page_title="MusicDSL Compiler", page_icon="🎵", layout="wide")
st.title("🎵 MusicDSL: A Compile-Time Music Generation DSL")

EXAMPLES_DIR = "examples"
example_files = sorted(
    f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".mdsl")
) if os.path.isdir(EXAMPLES_DIR) else []

choice = st.sidebar.selectbox("Load an example", ["(blank)"] + example_files)
default_code = ""
if choice != "(blank)":
    with open(os.path.join(EXAMPLES_DIR, choice), encoding="utf-8") as handle:
        default_code = handle.read()

left, right = st.columns(2)
with left:
    source = st.text_area("Source code", value=default_code, height=420,
                          key=f"editor_{choice}")
    compile_clicked = st.button("Compile", type="primary")

with right:
    if compile_clicked:
        with tempfile.TemporaryDirectory() as folder:
            src_path = os.path.join(folder, "song.mdsl")
            mid_path = os.path.join(folder, "song.mid")
            xml_path = os.path.join(folder, "song.musicxml")
            wav_path = os.path.join(folder, "song.wav")
            with open(src_path, "w", encoding="utf-8") as handle:
                handle.write(source)
            try:
                result = compile_file(src_path, mid_path)
                write_musicxml(result.ir, xml_path)
                write_wav(result.ir, wav_path)
            except LexicalError as error:
                st.error(str(error))
            except ParserError as error:
                st.error(str(error))
            except SemanticError as error:
                st.error(str(error))
            else:
                st.success(f"Compiled: {len(result.ir.events)} events, "
                           f"{result.ir.total_beats} beats")
                for warning in result.warnings:
                    st.warning(str(warning))
                with open(wav_path, "rb") as handle:
                    wav_bytes = handle.read()
                with open(mid_path, "rb") as handle:
                    mid_bytes = handle.read()
                with open(xml_path, "rb") as handle:
                    xml_bytes = handle.read()
                st.audio(wav_bytes, format="audio/wav")
                st.download_button("Download MIDI", mid_bytes, "song.mid")
                st.download_button("Download WAV", wav_bytes, "song.wav")
                st.download_button("Download MusicXML", xml_bytes, "song.musicxml")
                with st.expander("Intermediate representation", expanded=True):
                    st.code(format_ir(result.ir))
    else:
        st.info("Write or load a program, then press Compile.")

