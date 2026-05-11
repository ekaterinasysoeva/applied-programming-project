import streamlit as st
import requests

URL= "https://naas.isalman.dev/no"

def request_no():
    response = requests.get(URL)
    response_json = response.json()
    return response_json["reason"]

if "text1" not in st.session_state:
    st.session_state["text1"] = request_no()
    print("init Text1")

if "text" not in st.session_state:
    st.session_state["text"] = request_no()
    print("init Text")


name = st.text_input("Name", placeholder="Hier Name eingeben...")
st.write(name)



if st.button("Neuer Text"):
    st.session_state["text"] = request_no()

st.write(st.session_state["text"])


if st.button("Neuer Text1"):
    st.session_state["text1"] = request_no()

st.write(st.session_state["text1"])

   
    
with st.expander("session_state"):
    st.write(st.session_state)


# ─────────────────────────────────────────────
# Notes API
# ─────────────────────────────────────────────

API_URL = "http://127.0.0.1:8000"

st.divider()
st.title("📝 Notes App")

# ── Function 1: Show all notes ──────────────

st.header("📋 All Notes")

def get_notes():
    try:
        response = requests.get(f"{API_URL}/notes")
        return response.json()
    except Exception:
        st.error("API is not running! Start it with: uv run fastapi dev")
        return []

notes = get_notes()

if notes:
    titles = [f"{note['id']} — {note['title']}" for note in notes]
    selected = st.selectbox("Select a note to view:", titles)

    selected_id = int(selected.split(" — ")[0])
    selected_note = next(n for n in notes if n["id"] == selected_id)

    with st.expander("📄 Note Details", expanded=True):
        st.write(f"**Title:** {selected_note['title']}")
        st.write(f"**Category:** {selected_note['category']}")
        st.write(f"**Tags:** {', '.join(selected_note['tags']) if selected_note['tags'] else '—'}")
        st.write(f"**Created:** {selected_note['created_at']}")
        st.write("**Content:**")
        st.write(selected_note['content'])
else:
    st.info("No notes yet. Create one below!")

st.divider()

# ── Function 2: Create a new note ───────────

st.header("➕ Create New Note")

with st.form("create_note_form"):
    title = st.text_input("Title", placeholder="Enter note title...")
    content = st.text_area("Content", placeholder="Enter note content...")
    category = st.selectbox("Category", ["general", "work", "personal", "school", "ideas"])
    tags_input = st.text_input("Tags (comma separated)", placeholder="e.g. python, work, urgent")

    submitted = st.form_submit_button("Create Note")

    if submitted:
        tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
        if category == "work" and "work" not in tags:
            tags.append("work")

        if not title or not content:
            st.error("Title and Content are required!")
        else:
            response = requests.post(f"{API_URL}/notes", json={
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
            })
            if response.status_code == 201:
                st.success(f"✅ Note '{title}' created!")
                st.rerun()
            else:
                st.error(f"❌ Error: {response.json()}")
                