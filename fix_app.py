import re

with open('app2.py', 'r', encoding='utf-8') as f:
    code = f.read()

css_old = \"\"\"# ?n UI m?c d?nh c?a Streamlit (gi? l?i Sidebar cho History)
st.markdown(\"\"\\\"
<style>
    #MainMenu, footer, header,
    [data-testid=\"stToolbar\"],
    [data-testid=\"stDecoration\"],
    [data-testid=\"stStatusWidget\"],
    [data-testid=\"stHeader\"] { display: none !important; }

    .block-container,
    [data-testid=\"stMainBlockContainer\"] {
        padding: 1rem !important;
        max-width: 100% !important;
        overflow: hidden;
    }

    [data-testid=\"stCustomComponentV1\"] iframe {
        height: 85vh !important;
        border: none !important;
    }
</style>
\"\"\\\", unsafe_allow_html=True)\"\"\"

css_new = \"\"\"# ?n toàn b? UI m?c d?nh c?a Streamlit
st.markdown(\"\"\\\"
<style>
    #MainMenu, footer, header,
    [data-testid=\"stToolbar\"],
    [data-testid=\"stDecoration\"],
    [data-testid=\"stStatusWidget\"],
    [data-testid=\"stHeader\"] { display: none !important; }

    .stApp { overflow: hidden; }

    .block-container,
    [data-testid=\"stMainBlockContainer\"] {
        padding: 0 !important;
        max-width: 100% !important;
        overflow: hidden;
    }

    /* Ðua iframe component chi?m full viewport */
    [data-testid=\"stCustomComponentV1\"],
    [data-testid=\"stCustomComponentV1\"] > div,
    [data-testid=\"stCustomComponentV1\"] iframe {
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        z-index: 999;
    }
</style>
\"\"\\\", unsafe_allow_html=True)\"\"\"

code = code.replace(css_old, css_new)

with open('app2.py', 'w', encoding='utf-8') as f:
    f.write(code)
