# sticky_nav.py — Streamlit JS Eval Version
from streamlit_js_eval import streamlit_js_eval
import streamlit as st


def render_sticky_nav(tabs, active_tab_key, lang="ne"):
    """
    Interactive sticky navigation — JavaScript-based
    
    Args:
        tabs: list of dicts [{"key": "chat", "label": "💬 Chat"}, ...]
        active_tab_key: current tab key
        lang: language
    
    Returns:
        Selected tab key (वा None यदि क्लिक भएन)
    """
    
    # Build CSS
    st.markdown("""
    <style>
        /* Nav container sticky */
        div[data-testid="stCustomComponentV1"] {
            position: sticky !important;
            top: 105px !important;
            z-index: 999 !important;
        }
        
        /* Nav buttons */
        .sticky-nav-wrapper {
            display: flex;
            gap: 8px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 10px 12px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
            border-left: 4px solid #667eea;
        }
        
        .nav-btn {
            flex: 1;
            padding: 12px 8px;
            font-size: 0.95rem;
            font-weight: 600;
            border: 2px solid #e0e0e0;
            background: #f8f9fa;
            color: #333;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            background: #f0f0ff;
            border-color: #667eea;
            color: #667eea;
            transform: translateY(-2px);
        }
        
        .nav-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Build buttons HTML
    buttons_html = ""
    for tab in tabs:
        is_active = "active" if tab["key"] == active_tab_key else ""
        buttons_html += f'<button class="nav-btn {is_active}" onclick="window.parent.postMessage({{type:\'streamlit:setComponentValue\',value:\'{tab["key"]}\'}},\'*\')">{tab["label"]}</button>'
    
    # Render as HTML component
    import streamlit.components.v1 as components
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; overflow: hidden; }}
            .sticky-nav {{
                display: flex;
                gap: 8px;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 10px 12px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                border-left: 4px solid #667eea;
            }}
            .nav-btn {{
                flex: 1;
                padding: 12px 8px;
                font-size: 0.95rem;
                font-weight: 600;
                border: 2px solid #e0e0e0;
                background: #f8f9fa;
                color: #333;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-family: inherit;
            }}
            .nav-btn:hover {{
                background: #f0f0ff;
                border-color: #667eea;
                color: #667eea;
                transform: translateY(-2px);
            }}
            .nav-btn.active {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: transparent;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="sticky-nav">
            {buttons_html}
        </div>
        
        <script>
            const buttons = document.querySelectorAll('.nav-btn');
            buttons.forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    // Get button text
                    const tabName = e.target.innerText;
                    
                    // Send to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setFrameHeight',
                        height: 70
                    }}, '*');
                    
                    // Send value via postMessage
                    const data = {{
                        type: 'streamlit:setComponentValue',
                        value: e.target.getAttribute('data-key'),
                        dataType: 'string'
                    }};
                    window.parent.postMessage(data, '*');
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html, height=70, scrolling=False)