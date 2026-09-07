import streamlit as st
import json
import re
import time
import urllib.parse
from groq import Groq
import streamlit.components.v1 as components
from youtube_transcript_api import YouTubeTranscriptApi

# Page configuration
st.set_page_config(page_title="Moonshadow X Auto-Generator", page_icon="🌙", layout="centered")

st.title("🌙 Moonshadow X Auto-Generator")
st.write("Generate trending posts inspired by current X conversations or YouTube video dialogues using your campaign keywords and hashtag.")

# 1. SECURITY: Load Groq API key safely
api_key = st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ System Configuration Error: Missing `GROQ_API_KEY` in Streamlit Secrets. Please add it to Settings -> Secrets.")
    st.stop()

try:
    client = Groq(api_key=api_key.strip())
except Exception as e:
    st.error(f"Failed to configure Groq client: {str(e)}")
    st.stop()

# 2. SESSION STATE MANAGEMENT
if "last_generation_time" not in st.session_state:
    st.session_state.last_generation_time = 0

if "previous_tweets" not in st.session_state:
    st.session_state.previous_tweets = []

# --- USER INPUTS ---
col1, col2 = st.columns(2)

with col1:
    keywords = st.text_input(
        "Trending Keywords (Line 2)", 
        value="CHAN BETWEEN KEY AND JAY",
        help="Campaign keywords to include."
    )

with col2:
    hashtags = st.text_input(
        "Episode Hashtag (Line 3)", 
        value="#MoonshadowSeriesEP5",
        help="Campaign hashtag to include."
    )

twist_angle = st.selectbox("Tone / Focus Angle", [
    "Puns & Funny Spins",
    "Pure Stan Hype & Screaming",
    "Sarcastic / Unhinged Reactions",
    "Theory, Angst & Plot Suspense",
    "Emotional & Character Dynamic Analysis"
])

# --- GENERATION INSPIRATION SOURCE OPTION ---
st.markdown("### 🔍 Choose Generation Inspiration Source")
inspiration_source = st.radio(
    "Select where to draw the generative inspiration from:",
    [
        "1) use hashtag only",
        "2) use the complete exact same keyword string + hashtag",
        "3) analyze youtube dialog",
        "4) user hashtag and youtube links"
    ],
    index=0,
    label_visibility="collapsed"
)

youtube_transcripts_text = ""
if "youtube" in inspiration_source.lower():
    st.markdown("#### 📺 YouTube Video Subtitles / Transcripts")
    st.caption("Paste up to 4 YouTube links below (one per line or comma-separated) to feed their dialogue into the prompt generation.")
    
    yt_input = st.text_area(
        "YouTube Links",
        value="",
        placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...",
        height=100
    )
    
    if yt_input.strip():
        urls = [url.strip() for url in re.split(r'[\n,\s]+', yt_input) if url.strip()]
        extracted_transcripts = []
        
        for url in urls[:4]:
            try:
                video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
                if video_id_match:
                    vid_id = video_id_match.group(1)
                    
                    try:
                        transcript_list = YouTubeTranscriptApi().fetch(vid_id, languages=['en', 'zh-Hant', 'zh-HK', 'th'])
                    except Exception:
                        transcript_list = YouTubeTranscriptApi().fetch(vid_id)
                        
                    full_transcript = " ".join([getattr(t, 'text', str(t)) for t in transcript_list])
                    extracted_transcripts.append(f"Source URL ({url}):\n{full_transcript[:3000]}")
            except Exception as e:
                st.warning(f"Could not fetch subtitles for {url} (Note: YouTube cloud hosting IP blocks can occur on public platforms): {str(e)}")
        
        if extracted_transcripts:
            youtube_transcripts_text = "\n\n".join(extracted_transcripts)
            st.success(f"Successfully loaded and parsed subtitles from {len(extracted_transcripts)} YouTube video(s)!")

# --- LANGUAGE CHECKBOXES ---
st.markdown("### 🌐 Select Language(s)")
col_lang1, col_lang2 = st.columns(2)

with col_lang1:
    lang_en = st.checkbox("🇬🇧 English", value=True)

with col_lang2:
    lang_hk = st.checkbox("🇭🇰 HK Cantonese", value=True)

if not lang_en and not lang_hk:
    st.warning("⚠️ Please select at least one language option.")

# --- HELPER: ACTION BUTTONS COMPONENT ---
def render_action_buttons(full_text, button_idx):
    encoded_tweet = urllib.parse.quote(full_text)
    tweet_url = f"https://x.com/intent/tweet?text={encoded_tweet}"
    
    js_safe_text = json.dumps(full_text)
    
    html_code = f"""
    <div style="display: flex; gap: 10px; align-items: center; margin-top: 8px;">
        <a href="{tweet_url}" target="_blank" style="
            background-color: #1d9bf0; 
            color: white; 
            padding: 8px 16px; 
            text-decoration: none; 
            border-radius: 20px; 
            font-size: 14px; 
            font-weight: bold;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: inline-block;">
            🚀 Tweet Option #{button_idx}
        </a>
        <button id="copy-btn-{button_idx}" onclick='copyToClipboard({js_safe_text}, "copy-btn-{button_idx}")' style="
            background-color: #2f3336; 
            color: white; 
            padding: 8px 16px; 
            border: 1px solid #53575b; 
            border-radius: 20px; 
            font-size: 14px; 
            font-weight: bold;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            📋 Copy
        </button>
    </div>

    <script>
    function copyToClipboard(text, btnId) {{
        navigator.clipboard.writeText(text).then(function() {{
            var btn = document.getElementById(btnId);
            var originalText = btn.innerHTML;
            btn.innerHTML = "✅ Copied!";
            btn.style.backgroundColor = "#00ba7c";
            setTimeout(function() {{
                btn.innerHTML = originalText;
                btn.style.backgroundColor = "#2f3336";
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Could not copy text: ', err);
        }});
    }}
    </script>
    """
    components.html(html_code, height=50)

# --- DYNAMIC CHARACTER LIMIT CALCULATION ---
keywords_clean = keywords.strip()
hashtags_clean = hashtags.strip()

lines_overhead = 3 if (keywords_clean and hashtags_clean) else 2
suffix_length = len(keywords_clean) + len(hashtags_clean) + lines_overhead
max_post_length = max(50, 280 - suffix_length)

st.caption(f"📏 Max text length per post: **{max_post_length} characters** (leaving room for keywords and hashtags within X's 280 limit).")

if keywords_clean or hashtags_clean:
    search_query = f"{keywords_clean} {hashtags_clean}".strip()
    x_search_url = f"https://x.com/search?q={urllib.parse.quote(search_query)}&f=live"
    st.markdown(f"🔍 [Click here to view live posts on X.com for `{search_query}`]({x_search_url})")

st.markdown("---")

# --- GENERATION LOGIC ---
btn_disabled = not (lang_en or lang_hk)

if st.button("🔥 Generate Posts", type="primary", disabled=btn_disabled):
    current_time = time.time()
    cooldown_seconds = 5
    
    if current_time - st.session_state.last_generation_time < cooldown_seconds:
        wait_time = int(cooldown_seconds - (current_time - st.session_state.last_generation_time))
        st.warning(f"⏳ Please wait {wait_time} seconds before generating again.")
    elif not keywords_clean and not hashtags_clean:
        st.warning("Please enter at least keywords or a hashtag.")
    else:
        st.session_state.last_generation_time = current_time
        
        instructions = []
        total_requested = 0

        if lang_en and lang_hk:
            total_requested = 20
            instructions.append("""
            - POSTS 1-10 (Native English Fandom Style):
              Written in authentic Stan Twitter / X style (casual, lowercase emphasis, natural reactions).
            - POSTS 11-20 (Hong Kong Cantonese Fandom Style):
              Written in natural HK Cantonese (spoken HK Chinese / 廣東話) as used on Threads/X.
              CRITICAL: DO NOT TRANSLATE or rephrase Posts 1-10. These must be completely original Cantonese ideas.
            """)
        elif lang_en:
            total_requested = 10
            instructions.append("""
            - POSTS 1-10 (Native English Fandom Style):
              Written in authentic Stan Twitter / X style (casual, lowercase emphasis, natural reactions).
            """)
        elif lang_hk:
            total_requested = 10
            instructions.append("""
            - POSTS 1-10 (Hong Kong Cantonese Fandom Style):
              Written in natural HK Cantonese (spoken HK Chinese / 廣東話) as used on Threads/X.
            """)

        # Configure Inspiration Directive based on user selection
        if inspiration_source.startswith("1)"):
            inspiration_directive = f"Inspiration Mode: Reference live online social discourse and trend sentiment anchored exclusively around the hashtag '{hashtags_clean}'."
        elif inspiration_source.startswith("2)"):
            inspiration_directive = f"Inspiration Mode: Reference live online social discourse and trend sentiment anchored around the complete exact keyword string '{keywords_clean}' combined with hashtag '{hashtags_clean}'."
        elif inspiration_source.startswith("3)"):
            inspiration_directive = f"Inspiration Mode: Use the following YouTube video subtitle/dialogue transcripts as the core thematic background and storyline context for generating the posts:\n{youtube_transcripts_text}"
        elif inspiration_source.startswith("4)"):
            inspiration_directive = f"Inspiration Mode: Combine both the hashtag '{hashtags_clean}' context and the following YouTube video subtitle/dialogue transcripts as the core thematic background:\n{youtube_transcripts_text}"
        else:
            inspiration_directive = f"Inspiration Mode: Reference live online social discourse and trend sentiment anchored around '{hashtags_clean}'."

        history_context = ""
        if st.session_state.previous_tweets:
            recent_tweets = st.session_state.previous_tweets[-30:]
            history_list = "\n".join([f"- {t}" for t in recent_tweets])
            history_context = f"""
            DO NOT REPEAT OR PARAPHRASE ANY OF THESE PREVIOUSLY GENERATED POSTS:
            {history_list}
            """

        prompt = f"""
        You are a top social media trend strategist and superfan for the TV series 'Moonshadow'.
        Your task is to generate FRESH, DISTINCT, high-engagement posts for X (Twitter).
        
        MANDATORY REQUIREMENT:
        - Every generated post MUST be designed to complement and contextually frame the required keyword string: "{keywords_clean}" and hashtag: "{hashtags_clean}".
        - {inspiration_directive}

        PARAMETERS:
        - Focus Angle: {twist_angle}
        - Max text body length per post: {max_post_length} characters.

        OUTPUT REQUIREMENTS:
        Generate EXACTLY {total_requested} unique posts.
        {"".join(instructions)}

        STRICT DIVERSITY RULE:
        {history_context}
        - Every post body must explore a different angle, joke, theory, or reaction.
        - DO NOT include the campaign keywords or hashtags inside the text body itself (they will be appended automatically via suffix).

        CRITICAL DIRECTIVE:
        Output MUST be strictly a valid JSON array of EXACTLY {total_requested} strings. Return ONLY the raw JSON array. Do not include markdown code blocks (like ```json), introduction, or extra text.
        """

        with st.spinner("Generating fresh posts with Groq (openai/gpt-oss-120b)..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a specialized social media JSON generation engine. You always output strictly valid JSON arrays containing only string elements without extra commentary."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.8,
                )

                raw_content = chat_completion.choices[0].message.content.strip()
                clean_json = re.sub(r'^
