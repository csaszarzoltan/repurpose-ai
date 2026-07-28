"""All format prompt templates for RepurposeAI.

Defines ALL_TEMPLATES — a list of 20 FormatTemplate instances covering
all supported content formats (8 existing + 12 new from Phase 2).
"""

from __future__ import annotations

from app.models.content import ContentFormat
from app.services.formats.registry import FormatTemplate

# ── Blog Post ─────────────────────────────────────────────────────────────

BLOG_POST = FormatTemplate(
    format_id=ContentFormat.BLOG_POST,
    name="Blog Post",
    description="Long-form content for blogs",
    max_length=5000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Professional, engaging, and authoritative",
    structure_hints="Introduction → H2 sections with headings → bullet points → conclusion → CTA",
    target_audience="General readers interested in the topic",
    system_prompt=(
        "You are an expert blog writer. Your writing is clear, engaging, "
        "and well-structured. You use subheadings, bullet points, and "
        "examples to make complex topics accessible. You end with a "
        "memorable conclusion and a call-to-action."
    ),
    user_prompt_template=(
        "Write a comprehensive blog post based on the source material below.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Twitter Thread ────────────────────────────────────────────────────────

TWITTER_THREAD = FormatTemplate(
    format_id=ContentFormat.TWITTER_THREAD,
    name="Twitter Thread",
    description="Multi-tweet thread for Twitter/X",
    max_length=1400,
    supports_images=True,
    supports_links=True,
    tone_guidance="Conversational, punchy, and opinionated",
    structure_hints="Hook tweet → numbered points → insight → CTA",
    target_audience="Twitter/X users seeking quick insights",
    system_prompt=(
        "You are a Twitter thread writer. You condense ideas into "
        "bite-sized, shareable tweets. Each tweet hooks the reader and "
        "the next builds on it. You use short sentences, emojis sparingly, "
        "and end with a strong takeaway."
    ),
    user_prompt_template=(
        "Turn the following content into a Twitter thread (5-10 tweets).\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── LinkedIn Post ─────────────────────────────────────────────────────────

LINKEDIN_POST = FormatTemplate(
    format_id=ContentFormat.LINKEDIN_POST,
    name="LinkedIn Post",
    description="Professional post for LinkedIn",
    max_length=3000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Professional, thought-leadership, and authentic",
    structure_hints="Hook → personal story/insight → key takeaways → CTA",
    target_audience="LinkedIn professionals and industry peers",
    system_prompt=(
        "You are a LinkedIn content creator. You write professional, "
        "thought-leadership posts that showcase expertise. You use "
        "short paragraphs, line breaks for readability, and include "
        "a clear call-to-action. You avoid jargon and keep it authentic."
    ),
    user_prompt_template=(
        "Create a LinkedIn post based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Newsletter ────────────────────────────────────────────────────────────

NEWSLETTER = FormatTemplate(
    format_id=ContentFormat.NEWSLETTER,
    name="Newsletter",
    description="Email newsletter content",
    max_length=10000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Friendly, personal, and value-driven",
    structure_hints="Greeting → main story/topic → quick hits → CTA → sign-off",
    target_audience="Email subscribers who opted in",
    system_prompt=(
        "You are a newsletter writer. You write in a warm, personal voice "
        "as if writing to a friend. You balance valuable insights with "
        "engaging storytelling. You use short paragraphs, include a "
        "clear subject line preview, and end with a sign-off that "
        "encourages continued engagement."
    ),
    user_prompt_template=(
        "Write a newsletter edition based on the source material.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Video Script ──────────────────────────────────────────────────────────

VIDEO_SCRIPT = FormatTemplate(
    format_id=ContentFormat.VIDEO_SCRIPT,
    name="Video Script",
    description="Script for video production",
    max_length=5000,
    supports_images=False,
    supports_links=False,
    tone_guidance="Conversational, visual, and dynamic",
    structure_hints="Hook → context → main content → demonstration → CTA",
    target_audience="Video viewers on YouTube or social platforms",
    system_prompt=(
        "You are a video script writer. You write for the ear, not the eye. "
        "Sentences are short and conversational. You include visual cues "
        "[in brackets] for the editor. You pace the script with natural "
        "pauses and build toward a clear takeaway."
    ),
    user_prompt_template=(
        "Write a video script based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Podcast Outline ───────────────────────────────────────────────────────

PODCAST_OUTLINE = FormatTemplate(
    format_id=ContentFormat.PODCAST_OUTLINE,
    name="Podcast Outline",
    description="Outline structure for podcast episodes",
    max_length=3000,
    supports_images=False,
    supports_links=True,
    tone_guidance="Structured, guiding, and conversational",
    structure_hints="Intro → topic overview → segment 1 → segment 2 → key takeaways → outro",
    target_audience="Podcast hosts planning episodes",
    system_prompt=(
        "You are a podcast outline creator. You structure episodes "
        "with clear segments, timing suggestions, and talking points. "
        "Each segment has a purpose and flows naturally into the next. "
        "You include suggested questions for interviews or discussion prompts."
    ),
    user_prompt_template=(
        "Create a podcast outline from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Email Sequence ────────────────────────────────────────────────────────

EMAIL_SEQUENCE = FormatTemplate(
    format_id=ContentFormat.EMAIL_SEQUENCE,
    name="Email Sequence",
    description="Multi-part email drip campaign",
    max_length=8000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Nurturing, persuasive, and value-first",
    structure_hints="Welcome → value delivery → social proof → offer → follow-up → close",
    target_audience="Email list subscribers in a nurture sequence",
    system_prompt=(
        "You are an email sequence writer. You craft multi-part drip "
        "campaigns that educate, nurture, and convert. Each email has "
        "a single focus, a clear subject line, and a specific CTA. "
        "You build anticipation across the sequence while always "
        "delivering value."
    ),
    user_prompt_template=(
        "Write an email sequence (3-5 emails) based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Social Media ──────────────────────────────────────────────────────────

SOCIAL_MEDIA = FormatTemplate(
    format_id=ContentFormat.SOCIAL_MEDIA,
    name="Social Media",
    description="Short social media post",
    max_length=500,
    supports_images=True,
    supports_links=True,
    tone_guidance="Concise, catchy, and platform-native",
    structure_hints="Hook → body → CTA (with hashtags where appropriate)",
    target_audience="Social media platform users",
    system_prompt=(
        "You are a social media content creator. You write short, "
        "attention-grabbing posts optimized for the platform. Every "
        "word earns its place. You use line breaks for scannability "
        "and include a clear CTA or question to drive engagement."
    ),
    user_prompt_template=(
        "Create a social media post from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ═══════════════════════════════════════════════════════════════════════════
# NEW PHASE 2 FORMATS
# ═══════════════════════════════════════════════════════════════════════════

# ── YouTube / TikTok Caption ──────────────────────────────────────────────

YOUTUBE_TIKTOK_CAPTION = FormatTemplate(
    format_id=ContentFormat.YOUTUBE_TIKTOK_CAPTION,
    name="YouTube/TikTok Caption",
    description="Short-form video caption for YouTube Shorts or TikTok",
    max_length=300,
    supports_images=False,
    supports_links=False,
    tone_guidance="Energetic, punchy, and hook-driven",
    structure_hints="Hook → quick context → payoff → engagement CTA",
    target_audience="Short-form video viewers (YouTube Shorts / TikTok)",
    system_prompt=(
        "You write captions for short-form video platforms. Every "
        "character counts. Start with a curiosity gap or bold statement. "
        "Keep it under 300 characters. Use line breaks, emojis sparingly, "
        "and end with a question or CTA to drive comments."
    ),
    user_prompt_template=(
        "Write a short video caption based on the content below.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Instagram Carousel ────────────────────────────────────────────────────

INSTAGRAM_CAROUSEL = FormatTemplate(
    format_id=ContentFormat.INSTAGRAM_CAROUSEL,
    name="Instagram Carousel",
    description="Multi-slide Instagram carousel post",
    max_length=2200,
    supports_images=True,
    supports_links=False,
    tone_guidance="Visual-first, educational, and scroll-stopping",
    structure_hints="Cover slide title → numbered educational slides → final CTA slide",
    target_audience="Instagram users interested in visual learning",
    system_prompt=(
        "You write Instagram carousel scripts. Structure the content "
        "into slides with a compelling cover, educational body slides, "
        "and a closing call-to-action. Each slide has a headline and "
        "2-3 bullet points. Write visually — describe what each slide "
        "shows. Keep captions tight and value-packed."
    ),
    user_prompt_template=(
        "Create an Instagram carousel (5-10 slides) from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Medium Article ────────────────────────────────────────────────────────

MEDIUM_ARTICLE = FormatTemplate(
    format_id=ContentFormat.MEDIUM_ARTICLE,
    name="Medium Article",
    description="Long-form article for Medium publication",
    max_length=10000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Reflective, authoritative, and story-driven",
    structure_hints="Compelling title → subtitle → opening anecdote → body sections → reflection → clap/comment CTA",
    target_audience="Medium readers seeking depth and insight",
    system_prompt=(
        "You write Medium articles with depth and personality. Start "
        "with a personal story or bold insight that hooks the reader. "
        "Use subheadings, pull quotes, and short paragraphs for "
        "readability. Include actionable takeaways. End by inviting "
        "claps and comments."
    ),
    user_prompt_template=(
        "Write a Medium article based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Reddit Post ───────────────────────────────────────────────────────────

REDDIT_POST = FormatTemplate(
    format_id=ContentFormat.REDDIT_POST,
    name="Reddit Post",
    description="Post for Reddit communities",
    max_length=40000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Authentic, conversational, and community-aware",
    structure_hints="Catchy title → context → personal take → discussion prompt",
    target_audience="Reddit community members in a specific subreddit",
    system_prompt=(
        "You write Reddit posts that feel authentic and human. "
        "Each subreddit has its own culture — adapt tone accordingly. "
        "Start with context, share your perspective or experience, "
        "and end with a question to spark discussion. Avoid marketing "
        "language and self-promotion."
    ),
    user_prompt_template=(
        "Write a Reddit post based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Landing Page ──────────────────────────────────────────────────────────

LANDING_PAGE = FormatTemplate(
    format_id=ContentFormat.LANDING_PAGE,
    name="Landing Page",
    description="Conversion-focused landing page copy",
    max_length=3000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Persuasive, benefit-driven, and clear",
    structure_hints="Hero headline → subheadline → pain points → solution → features/benefits → social proof → CTA → FAQ",
    target_audience="Potential customers evaluating a product or service",
    system_prompt=(
        "You write landing page copy that converts. Start with a "
        "headline that states the main benefit. Address pain points, "
        "present your solution, and back it with social proof. Use "
        "short paragraphs, bullet points, and clear CTAs. Every "
        "element should push toward the conversion goal."
    ),
    user_prompt_template=(
        "Write landing page copy based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Press Release ─────────────────────────────────────────────────────────

PRESS_RELEASE = FormatTemplate(
    format_id=ContentFormat.PRESS_RELEASE,
    name="Press Release",
    description="Official press release for media distribution",
    max_length=2000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Formal, factual, and newsworthy",
    structure_hints="FOR IMMEDIATE RELEASE → Headline → dateline → lead paragraph → body quotes → boilerplate → media contact",
    target_audience="Journalists, reporters, and media outlets",
    system_prompt=(
        "You write press releases in AP style. Lead with the most "
        "newsworthy information: who, what, when, where, why. Follow "
        "with a supporting quote from leadership. End with company "
        "boilerplate and media contact details. Keep it objective "
        "and fact-based."
    ),
    user_prompt_template=(
        "Write a press release based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Case Study ────────────────────────────────────────────────────────────

CASE_STUDY = FormatTemplate(
    format_id=ContentFormat.CASE_STUDY,
    name="Case Study",
    description="Customer success story case study",
    max_length=4000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Story-driven, results-focused, and credible",
    structure_hints="Title → customer background → challenge → solution → results → testimonial → CTA",
    target_audience="Prospective customers evaluating similar solutions",
    system_prompt=(
        "You write case studies that tell a compelling customer "
        "success story. Set up the customer's challenge, describe "
        "how the solution addressed it, and highlight measurable "
        "results. Include a direct quote from the customer. Use "
        "specific numbers and outcomes."
    ),
    user_prompt_template=(
        "Write a case study based on the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Whitepaper Outline ────────────────────────────────────────────────────

WHITEPAPER_OUTLINE = FormatTemplate(
    format_id=ContentFormat.WHITEPAPER_OUTLINE,
    name="Whitepaper Outline",
    description="Outline and structure for an in-depth whitepaper",
    max_length=5000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Academic, authoritative, and research-driven",
    structure_hints="Title → executive summary → problem statement → methodology → findings → analysis → conclusion → references",
    target_audience="Industry professionals, analysts, and decision-makers",
    system_prompt=(
        "You create whitepaper outlines for in-depth research content. "
        "Structure chapters logically: introduce the problem, present "
        "research methodology, share findings, discuss implications, "
        "and conclude with recommendations. Each chapter has clear "
        "objectives and proposed content."
    ),
    user_prompt_template=(
        "Create a whitepaper outline from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── eBook Chapter Plan ────────────────────────────────────────────────────

EBOOK_CHAPTER_PLAN = FormatTemplate(
    format_id=ContentFormat.EBOOK_CHAPTER_PLAN,
    name="eBook Chapter Plan",
    description="Structured chapter plan for an eBook",
    max_length=5000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Educational, encouraging, and structured",
    structure_hints="Title → chapter overview → learning objectives → section headings → key takeaways → exercises",
    target_audience="Readers looking to learn a topic in-depth",
    system_prompt=(
        "You plan eBook chapters that educate and guide. Each chapter "
        "has clear learning objectives, structured sections with "
        "headings, practical examples, and key takeaways. You write "
        "chapter descriptions that make the reader eager to dive in."
    ),
    user_prompt_template=(
        "Create an eBook chapter plan from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── Podcast Show Notes ────────────────────────────────────────────────────

PODCAST_SHOW_NOTES = FormatTemplate(
    format_id=ContentFormat.PODCAST_SHOW_NOTES,
    name="Podcast Show Notes",
    description="Show notes and summary for podcast episodes",
    max_length=2500,
    supports_images=False,
    supports_links=True,
    tone_guidance="Informative, scannable, and engaging",
    structure_hints="Episode title → brief summary → timestamped highlights → key quotes → resources → CTA",
    target_audience="Podcast listeners browsing episodes",
    system_prompt=(
        "You write podcast show notes that help listeners get value "
        "from episodes. Start with a compelling summary, include "
        "timestamped highlights for key topics, pull memorable quotes, "
        "and link to resources mentioned. Make it scannable so "
        "listeners can find what matters to them."
    ),
    user_prompt_template=(
        "Write podcast show notes from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── LinkedIn Carousel ─────────────────────────────────────────────────────

LINKEDIN_CAROUSEL = FormatTemplate(
    format_id=ContentFormat.LINKEDIN_CAROUSEL,
    name="LinkedIn Carousel",
    description="Multi-page carousel PDF post for LinkedIn",
    max_length=3000,
    supports_images=True,
    supports_links=True,
    tone_guidance="Professional, educational, and visually scannable",
    structure_hints="Title slide → problem → insight → data → solution → key takeaways → CTA slide",
    target_audience="LinkedIn connections and followers",
    system_prompt=(
        "You write LinkedIn carousel content. Each slide has a "
        "headline and 2-4 bullet points. The first slide hooks with "
        "a bold statement or question. Middle slides educate. The "
        "final slide includes a CTA. Describe visual elements for the "
        "designer. Keep text concise for easy reading on mobile."
    ),
    user_prompt_template=(
        "Create a LinkedIn carousel (5-8 slides) from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ── SaaS Changelog ────────────────────────────────────────────────────────

SAAS_CHANGELOG = FormatTemplate(
    format_id=ContentFormat.SAAS_CHANGELOG,
    name="SaaS Changelog",
    description="Product update and changelog entry",
    max_length=1500,
    supports_images=True,
    supports_links=True,
    tone_guidance="Clear, user-focused, and celebratory",
    structure_hints="Version/date → headline → what's new → improvements → bug fixes → upgrade CTA",
    target_audience="Existing SaaS product users and stakeholders",
    system_prompt=(
        "You write SaaS changelog entries that keep users informed "
        "and excited. Group changes into 'New', 'Improved', and "
        "'Fixed'. Lead with the biggest user-facing change. Write "
        "from the user's perspective — what does this mean for them? "
        "Keep technical details brief and link to docs for more."
    ),
    user_prompt_template=(
        "Write a SaaS changelog entry from the source content.\n\n"
        "Source content:\n{content}\n\n"
        "Additional instructions: {custom_instructions}\n"
        "Brand voice: {brand_voice}"
    ),
)

# ═══════════════════════════════════════════════════════════════════════════
# ALL_TEMPLATES: complete list of all 20 format templates
# ═══════════════════════════════════════════════════════════════════════════

ALL_TEMPLATES: list[FormatTemplate] = [
    # 8 existing formats
    BLOG_POST,
    TWITTER_THREAD,
    LINKEDIN_POST,
    NEWSLETTER,
    VIDEO_SCRIPT,
    PODCAST_OUTLINE,
    EMAIL_SEQUENCE,
    SOCIAL_MEDIA,
    # 12 new formats
    YOUTUBE_TIKTOK_CAPTION,
    INSTAGRAM_CAROUSEL,
    MEDIUM_ARTICLE,
    REDDIT_POST,
    LANDING_PAGE,
    PRESS_RELEASE,
    CASE_STUDY,
    WHITEPAPER_OUTLINE,
    EBOOK_CHAPTER_PLAN,
    PODCAST_SHOW_NOTES,
    LINKEDIN_CAROUSEL,
    SAAS_CHANGELOG,
]
