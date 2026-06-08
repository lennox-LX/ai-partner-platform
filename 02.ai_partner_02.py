#!/usr/bin/env python3
"""
AI 角色对话平台 v2 — 单人单角色会话 + 群聊模式 + 社区 + 用户系统
支持 DeepSeek / 千问 / 豆包 / 智谱 / Moonshot 等多种模型

模块索引（按职责分层，便于未来拆分多文件）
┌─    1- 600 行：全局 CSS 设计系统（Glassmorphism + OLED 深色主题）
├─  596- 692 行：常量配置（ROLE_TEMPLATES / MODEL_CONFIGS / 颜色）
├─  694- 768 行：工具函数 + 角色匹配（@提及 / 关键词路由）
├─  770- 826 行：LLM 客户端（多厂商适配器模式）
├─  795- 865 行：用户系统（注册 / 登录 / PBKDF2 密码存储）
├─  839- 925 行：社区管理（帖子 / 点赞 / 收藏 / 评论）
├─  926-1048 行：会话持久化（单人/群聊 save/load/export）
├─ 1050-1085 行：Prompt 构建 + LLM 调用封装
├─ 1086-1140 行：Session State 初始化 + 路由驱动
├─ 1142-1205 行：顶部导航栏
├─ 1206-1250 行：登录 / 注册对话框
├─ 1260-1620 行：侧边栏（角色/模型/会话/Token/导出）
├─ 1622-1775 行：社区广场 + 个人中心
├─ 1776-2010 行：AI 对话（单人 + 群聊 + 模型对比）
└─ 2005-2013 行：页脚
"""

import streamlit as st
import os
import json
import hashlib
import uuid
import re
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import tiktoken

# ============================================================
# 全局 CSS：动态渐变背景 + 浮动光斑 + 增强玻璃拟态
# ============================================================
st.markdown("""
<style>
    /* ================================================================
     * ETHEREAL GLASS — Awwwards-Tier Design System
     * Vibe: Deep OLED + radial mesh orbs + heavy blur glass
     * Motion: custom cubic-bezier throughout, zero linear/ease
     * ================================================================ */

    /* ===== 1. FOUNDATION: OLED Deep Space Background ===== */
    .stApp {
        background-color: #06080a;
        background-image:
            /* 柔粉玫瑰 右上 */
            radial-gradient(ellipse 70% 50% at 80% 10%, rgba(225,165,180,0.08) 0%, rgba(200,145,160,0.03) 30%, transparent 60%),
            /* 暖杏 右中 */
            radial-gradient(ellipse 55% 45% at 72% 50%, rgba(215,185,145,0.06) 0%, rgba(195,168,130,0.02) 30%, transparent 60%),
            /* 鼠尾草绿 左下 */
            radial-gradient(ellipse 60% 48% at 15% 85%, rgba(135,180,150,0.06) 0%, rgba(120,165,135,0.02) 30%, transparent 60%),
            /* 薰衣草 左上 */
            radial-gradient(ellipse 48% 38% at 25% 20%, rgba(180,150,205,0.05) 0%, rgba(160,135,185,0.02) 30%, transparent 55%),
            /* 天蓝 中上 */
            radial-gradient(ellipse 42% 30% at 50% 15%, rgba(145,180,210,0.05) 0%, rgba(130,165,195,0.02) 30%, transparent 55%),
            /* 薄荷绿 中下 */
            radial-gradient(ellipse 45% 35% at 55% 70%, rgba(140,190,170,0.04) 0%, transparent 55%),
            /* 底色渐变（多色过渡） */
            linear-gradient(170deg, #07090a 0%, #090c0d 25%, #0a0d0c 50%, #080b0a 75%, #060809 100%);
        background-size: 100% 100%;
        animation: bgBreathe 30s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }

    @keyframes bgBreathe {
        0%, 100% { background-position: 0% 0%; opacity: 1; }
        25%  { background-position: 2% 1.5%; }
        50%  { background-position: -1.5% 2%; }
        75%  { background-position: 1.5% -1%; }
    }

    /* ===== 2. AMBIENT ORBS: 4 Floating Light Sculptures ===== */
    .stApp::before {
        content: ''; position: fixed; top: -22%; right: -12%;
        width: 65vw; height: 65vw; max-width: 900px; max-height: 900px;
        background: radial-gradient(circle at 50% 50%,
            rgba(210,170,190,0.09) 0%, rgba(190,150,170,0.03) 30%, transparent 60%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: orbPrimary 22s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }
    .stApp::after {
        content: ''; position: fixed; bottom: -18%; left: -8%;
        width: 55vw; height: 55vw; max-width: 750px; max-height: 750px;
        background: radial-gradient(circle at 50% 50%,
            rgba(150,190,160,0.07) 0%, rgba(130,170,140,0.025) 30%, transparent 60%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: orbSecondary 25s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }
    .main::before {
        content: ''; position: fixed; top: 30%; left: 55%;
        width: 35vw; height: 35vw; max-width: 500px; max-height: 500px;
        background: radial-gradient(circle at 50% 50%,
            rgba(220,195,160,0.055) 0%, rgba(200,175,140,0.018) 30%, transparent 60%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: orbTertiary 19s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }
    .main::after {
        content: ''; position: fixed; top: 12%; left: 25%;
        width: 22vw; height: 22vw; max-width: 320px; max-height: 320px;
        background: radial-gradient(circle at 50% 50%,
            rgba(185,155,200,0.045) 0%, rgba(165,135,180,0.014) 30%, transparent 55%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: orbQuart 17s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }

    @keyframes orbPrimary {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25%  { transform: translate(5vw, -4vh) scale(1.12); }
        50%  { transform: translate(-3vw, 3vh) scale(0.92); }
        75%  { transform: translate(-5vw, -2vh) scale(1.06); }
    }
    @keyframes orbSecondary {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33%  { transform: translate(-4vw, -3vh) scale(1.18); }
        66%  { transform: translate(4vw, 4vh) scale(0.86); }
    }
    @keyframes orbTertiary {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50%  { transform: translate(-6vw, -5vh) scale(1.30); }
    }
    @keyframes orbQuart {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50%  { transform: translate(4vw, -3vh) scale(1.22); }
    }

    /* ===== 3. MICRO-TEXTURE: Subtle grain overlay ===== */
    .block-container { position: relative; z-index: 1; }
    .block-container::before {
        content: ''; position: fixed; inset: 0;
        background-image:
            radial-gradient(circle at 15% 25%, rgba(200,195,200,0.012) 0%, transparent 2.5%),
            radial-gradient(circle at 55% 65%, rgba(200,195,200,0.008) 0%, transparent 2%),
            radial-gradient(circle at 75% 12%, rgba(200,195,200,0.01) 0%, transparent 2.2%),
            radial-gradient(circle at 35% 80%, rgba(200,195,200,0.008) 0%, transparent 1.8%),
            radial-gradient(circle at 8% 55%, rgba(200,195,200,0.01) 0%, transparent 2.5%),
            radial-gradient(circle at 88% 45%, rgba(200,195,200,0.009) 0%, transparent 2%),
            radial-gradient(circle at 45% 15%, rgba(200,195,200,0.007) 0%, transparent 1.5%);
        background-size: 100% 100%;
        pointer-events: none; z-index: 0;
        animation: grainPulse 35s cubic-bezier(0.32, 0.72, 0, 1) infinite;
    }
    @keyframes grainPulse {
        0%, 100% { opacity: 0.5; }
        50%  { opacity: 1.0; }
    }

    /* ===== 4. SIDEBAR: Floating Glass Panel ===== */
    [data-testid="stSidebar"] {
        background: rgba(6, 8, 14, 0.72) !important;
        backdrop-filter: blur(40px) saturate(200%);
        -webkit-backdrop-filter: blur(40px) saturate(200%);
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.025),
            6px 0 48px rgba(0, 0, 0, 0.50);
    }
    [data-testid="stSidebar"] * { color: #bab5ae !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label { color: #d0cac4 !important; }

    /* ===== 5. ROLE LIST ITEMS: Magnetic List Cards ===== */
    .role-list-btn {
        display: flex; align-items: center; gap: 10px;
        width: 100%; padding: 10px 14px;
        background: rgba(255,255,255,0.015);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px; color: #a09b95; font-size: 14px;
        transition: all 0.5s cubic-bezier(0.32, 0.72, 0, 1);
        cursor: pointer; margin-bottom: 3px; text-align: left;
    }
    .role-list-btn:hover {
        background: rgba(140,120,180,0.08);
        border-color: rgba(140,120,180,0.18);
        color: #c8c3bd;
        transform: translateX(4px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }
    .role-list-btn.active {
        background: rgba(140,120,180,0.10);
        border-color: rgba(140,120,180,0.25);
        color: #c0b0e0;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 0 20px rgba(120,100,160,0.08);
    }
    .role-msg-count { font-size: 11px; color: #7a7570; margin-left: auto; }

    /* ===== 6. KEYFRAMES: All cubic-bezier, no linear/ease ===== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes fadeInChat {
        0%   { opacity: 0; transform: translateY(32px) scale(0.95); filter: blur(6px); }
        100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    @keyframes messageSlideIn {
        0%   { opacity: 0; transform: translateY(28px); filter: blur(4px); }
        100% { opacity: 1; transform: translateY(0); filter: blur(0); }
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to   { opacity: 1; transform: translateX(0); }
    }

    /* ===== 7. MAIN CONTENT: Breathe ===== */
    .main .block-container {
        animation: fadeIn 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        padding-top: 0.5rem !important;
        position: relative; z-index: 1;
    }

    /* ===== 8. CHAT BUBBLES: Double-Bezel Glass ===== */
    .stChatMessage {
        animation: messageSlideIn 0.75s cubic-bezier(0.16, 1, 0.3, 1) both;
        background: rgba(255,255,255,0.018) !important;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 18px !important;
        margin-bottom: 12px !important;
        padding: 12px 18px !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.025),
            0 4px 20px rgba(0,0,0,0.25);
        transition: all 0.5s cubic-bezier(0.32, 0.72, 0, 1);
    }
    .stChatMessage:hover {
        border-color: rgba(140,120,180,0.18) !important;
        background: rgba(255,255,255,0.028) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 6px 28px rgba(0,0,0,0.35);
    }
    .stChatMessage:nth-child(1)  { animation-delay: 0.04s; }
    .stChatMessage:nth-child(2)  { animation-delay: 0.10s; }
    .stChatMessage:nth-child(3)  { animation-delay: 0.16s; }
    .stChatMessage:nth-child(4)  { animation-delay: 0.22s; }
    .stChatMessage:nth-child(5)  { animation-delay: 0.28s; }
    .stChatMessage:nth-child(6)  { animation-delay: 0.34s; }
    .stChatMessage:nth-child(7)  { animation-delay: 0.40s; }
    .stChatMessage:nth-child(8)  { animation-delay: 0.46s; }
    .stChatMessage:nth-child(9)  { animation-delay: 0.52s; }
    .stChatMessage:nth-child(10) { animation-delay: 0.58s; }

    /* ===== 9. TITLE: Gradient Text ===== */
    .main-title {
        font-size: 1.6rem !important; font-weight: 700 !important;
        letter-spacing: -0.3px;
        background: linear-gradient(135deg, #c0a8e0, #90c0d8, #a0c8b0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: fadeIn 1.0s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .top-bar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 0; margin-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }

    /* ===== 10. BUTTONS: Magnetic Hover Physics ===== */
    .stButton > button {
        background: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 10px !important; color: #c5c0ba !important;
        font-weight: 500 !important; font-size: 13px !important;
        transition: all 0.45s cubic-bezier(0.32, 0.72, 0, 1) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }
    .stButton > button:hover {
        background: rgba(140,120,180,0.10) !important;
        border-color: rgba(140,120,180,0.22) !important;
        transform: translateY(-2px);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 8px 24px rgba(100,80,150,0.12);
    }
    .stButton > button:active {
        transform: scale(0.97);
        transition: all 0.15s cubic-bezier(0.32, 0.72, 0, 1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(140,110,190,0.18), rgba(100,140,190,0.14)) !important;
        border-color: rgba(140,120,180,0.20) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 4px 16px rgba(100,80,150,0.10);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, rgba(140,110,190,0.30), rgba(100,140,190,0.22)) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.06),
            0 8px 28px rgba(100,80,150,0.20);
    }

    /* ===== 11. INPUTS: Focus Glow ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.025) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 10px !important; color: #c5c0ba !important;
        transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(140,120,180,0.35) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.03),
            0 0 0 3px rgba(120,100,160,0.08);
    }
    .stChatInput {
        background: rgba(255,255,255,0.018) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.20);
    }
    .stChatInput:focus-within {
        border-color: rgba(140,120,180,0.30) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.03),
            0 0 0 4px rgba(120,100,160,0.06),
            0 4px 24px rgba(0,0,0,0.30);
    }
    .stChatInput textarea { color: #c5c0ba !important; }

    /* ===== 12. SELECT & DROPDOWNS ===== */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.025) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
    }

    /* ===== 13. ROLE CHIPS ===== */
    .role-chip {
        display: inline-block; padding: 3px 12px;
        border-radius: 16px; font-size: 12px; font-weight: 500;
        margin: 2px 4px;
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
    }

    /* ===== 14. GLASS CARDS: Double-Bezel Architecture ===== */
    .glass-card {
        background: rgba(255,255,255,0.018);
        backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px; padding: 20px; margin-bottom: 16px;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.025),
            0 4px 24px rgba(0,0,0,0.30);
        transition: all 0.5s cubic-bezier(0.32, 0.72, 0, 1);
        animation: slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .glass-card:hover {
        border-color: rgba(140,120,180,0.15);
        background: rgba(255,255,255,0.028);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 8px 32px rgba(0,0,0,0.40);
    }
    .post-card {
        background: rgba(255,255,255,0.015);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px; padding: 18px; margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        transition: all 0.5s cubic-bezier(0.32, 0.72, 0, 1);
    }
    .post-card:hover {
        border-color: rgba(140,120,180,0.15);
        background: rgba(255,255,255,0.028);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.03),
            0 8px 28px rgba(0,0,0,0.35);
    }

    /* ===== 15. DIVIDERS ===== */
    hr {
        margin: 18px 0; border: none; height: 1px;
        background: linear-gradient(to right, transparent, rgba(140,120,180,0.12), transparent);
    }

    /* ===== 16. SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }

    /* ===== 17. METRICS & ALERTS ===== */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.018);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 10px; padding: 8px 12px;
    }
    .stAlert {
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border-radius: 12px !important;
    }
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.018) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
    }

    /* ===== 18. TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background: rgba(255,255,255,0.015);
        border-radius: 12px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important; color: #706c67 !important;
        transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(140,120,180,0.10) !important;
        color: #c0b0e0 !important;
    }

    /* ===== 19. SLIDER ===== */
    .stSlider > div > div > div > div {
        background: rgba(140,120,180,0.25) !important;
    }

    /* ===== 20. CHAT FADE-IN CONTAINER ===== */
    .chat-fade-in {
        animation: fadeInChat 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    /* ===== 21. CHAT-AREA DECORATIONS: Soft blobs in center-right zone only ===== */
    .main .block-container { position: relative; }

    /* ── 柔粉椭圆：右上 ── */
    .main .block-container::after {
        content: '';
        position: fixed; top: 4%; right: 3%;
        width: 280px; height: 180px;
        background: radial-gradient(ellipse 58% 48% at 55% 35%,
            rgba(235,175,185,0.15) 0%, rgba(220,160,170,0.05) 35%, transparent 65%);
        border-radius: 40% 60% 55% 45%;
        animation: cBlob1 14s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob1 {
        0%, 100% { transform: translate(0, 0) rotate(0deg) scale(1); }
        25%  { transform: translate(-50px, -30px) rotate(3deg) scale(1.08); }
        50%  { transform: translate(-65px, 12px) rotate(-2deg) scale(0.92); }
        75%  { transform: translate(-20px, -40px) rotate(1deg) scale(1.05); }
    }

    /* ── 暖杏椭圆：中右 ── */
    .stChatInput::before {
        content: '';
        position: fixed; top: 35%; right: 5%;
        width: 160px; height: 110px;
        background: radial-gradient(ellipse 50% 55% at 50% 45%,
            rgba(225,195,150,0.15) 0%, rgba(210,180,135,0.05) 40%, transparent 65%);
        border-radius: 48% 52% 45% 55%;
        animation: cBlob2 10s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob2 {
        0%, 100% { transform: translate(0, 0) scale(0.85); opacity: 0.6; }
        50%  { transform: translate(-30px, -25px) scale(1.18); opacity: 1.0; }
    }

    /* ── 薰衣草椭圆：中上偏右 ── */
    .stChatInput::after {
        content: '';
        position: fixed; top: 22%; right: 18%;
        width: 130px; height: 150px;
        background: radial-gradient(ellipse 48% 52% at 48% 50%,
            rgba(190,165,210,0.13) 0%, rgba(175,150,195,0.04) 40%, transparent 65%);
        border-radius: 50% 52% 48% 50%;
        animation: cBlob3 11s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob3 {
        0%, 100% { transform: translate(0, 0) scale(0.80); opacity: 0.55; }
        50%  { transform: translate(30px, -35px) scale(1.18); opacity: 1.0; }
    }

    /* ── 天蓝小点：右下 ── */
    .block-container [data-testid="stVerticalBlock"]::before {
        content: '';
        position: fixed; bottom: 20%; right: 8%;
        width: 90px; height: 70px;
        background: radial-gradient(ellipse 50% 50% at 50% 50%,
            rgba(160,195,215,0.13) 0%, rgba(145,180,200,0.04) 40%, transparent 65%);
        border-radius: 50% 48% 45% 52%;
        animation: cBlob4 13s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob4 {
        0%, 100% { transform: translate(0, 0) scale(0.78); opacity: 0.50; }
        50%  { transform: translate(-25px, -25px) scale(1.22); opacity: 1.0; }
    }

    /* ── 暖灰小点：中右偏下 ── */
    .stHorizontalBlock::after {
        content: '';
        position: fixed; top: 55%; right: 22%;
        width: 65px; height: 65px;
        background: radial-gradient(circle at 50% 50%,
            rgba(185,178,172,0.13) 0%, rgba(170,163,157,0.04) 40%, transparent 65%);
        border-radius: 48% 52% 50% 50%;
        animation: cBlob5 8s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob5 {
        0%, 100% { transform: translate(0, 0) scale(0.72); opacity: 0.45; }
        50%  { transform: translate(-20px, 20px) scale(1.28); opacity: 1.0; }
    }

    /* ── 薄荷椭圆：聊天区中左 ── */
    .main .block-container::before {
        content: '';
        position: fixed; top: 38%; left: 52%;
        width: 80px; height: 100px;
        background: radial-gradient(ellipse 45% 55% at 50% 50%,
            rgba(170,210,190,0.11) 0%, rgba(155,195,175,0.03) 40%, transparent 65%);
        border-radius: 48% 52% 48% 52%;
        animation: cBlob6 9s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob6 {
        0%, 100% { transform: translate(0, 0) scale(0.75); opacity: 0.48; }
        50%  { transform: translate(18px, -25px) scale(1.25); opacity: 1.0; }
    }

    /* ── 珊瑚小圆：聊天区中右上方 ── */
    .stApp [data-testid="stVerticalBlock"]::after {
        content: '';
        position: fixed; top: 28%; right: 30%;
        width: 55px; height: 55px;
        background: radial-gradient(circle at 50% 50%,
            rgba(225,170,170,0.12) 0%, rgba(210,155,155,0.03) 40%, transparent 65%);
        border-radius: 50%;
        animation: cBlob7 7s cubic-bezier(0.32,0.72,0,1) infinite;
        pointer-events: none; z-index: 0;
    }
    @keyframes cBlob7 {
        0%, 100% { transform: translate(0, 0) scale(0.70); opacity: 0.42; }
        50%  { transform: translate(-15px, -20px) scale(1.28); opacity: 1.0; }
    }

    /* ── 顶部栏渐变装饰线 ── */
    .top-bar::after {
        content: '';
        position: absolute; bottom: -1px; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg,
            transparent, rgba(220,160,180,0.18), rgba(160,195,160,0.14),
            rgba(160,190,215,0.16), rgba(215,190,155,0.14), transparent);
    }

    /* ── 侧边栏底部装饰线 ── */
    [data-testid="stSidebar"]::after {
        content: '';
        position: absolute; bottom: 0; left: 12px; right: 12px;
        height: 1px;
        background: linear-gradient(90deg,
            transparent, rgba(185,180,175,0.08), rgba(160,170,180,0.08), transparent);
    }

    /* ── 聊天区渐变过渡遮罩 ── */
    .main .block-container {
        background:
            radial-gradient(ellipse 40% 30% at 70% 25%, rgba(200,180,190,0.025) 0%, transparent 60%),
            radial-gradient(ellipse 35% 25% at 65% 60%, rgba(180,195,185,0.020) 0%, transparent 55%);
    }

    /* ── 注入式装饰元素 ── */
    .deco-dot { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; }
    .deco-dot-1 {
        top: 18%; right: 12%; width: 6px; height: 6px;
        background: rgba(220,180,190,0.35);
        animation: dotFloat1 5s cubic-bezier(0.32,0.72,0,1) infinite;
    }
    .deco-dot-2 {
        top: 48%; right: 20%; width: 4px; height: 4px;
        background: rgba(180,200,210,0.30);
        animation: dotFloat2 6s cubic-bezier(0.32,0.72,0,1) infinite;
    }
    .deco-dot-3 {
        top: 62%; right: 8%; width: 5px; height: 5px;
        background: rgba(210,195,170,0.32);
        animation: dotFloat3 7s cubic-bezier(0.32,0.72,0,1) infinite;
    }
    @keyframes dotFloat1 {
        0%, 100% { transform: translate(0, 0); opacity: 0.5; }
        50%  { transform: translate(-12px, -18px); opacity: 1.0; }
    }
    @keyframes dotFloat2 {
        0%, 100% { transform: translate(0, 0); opacity: 0.4; }
        50%  { transform: translate(10px, -14px); opacity: 0.9; }
    }
    @keyframes dotFloat3 {
        0%, 100% { transform: translate(0, 0); opacity: 0.45; }
        50%  { transform: translate(-8px, 15px); opacity: 0.95; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 常量配置
# ============================================================

ROLE_TEMPLATES = [
    {
        "id": "code_reviewer", "name": "代码审查员", "icon": "💻",
        "mention": "@代码审查员", "color": "#8cb8d8",
        "system_prompt": (
            "我是资深代码审查专家，拥有10年以上全栈开发经验。"
            "审查代码时请重点关注：安全漏洞、性能瓶颈、代码异味、最佳实践偏离。"
            "回复要简洁专业，一针见血，直接指出问题行和具体改进方案。"
            "使用「🔴严重/🟡警告/🟢建议」分级标注。"
        ),
        "keywords": "代码 编程 bug debug 函数 类 算法 重构 优化 python java javascript"
                    " 报错 异常 error exception api 接口 框架 sql 数据库 前端 后端 react vue"
                    " typescript rust go 测试 部署 docker",
    },
    {
        "id": "translator", "name": "翻译专家", "icon": "🌐",
        "mention": "@翻译专家", "color": "#b8a0d0",
        "system_prompt": (
            "我是专业翻译专家，精通中/英/日/韩/法/德/西等主流语言。"
            "翻译时保留原文风格、语气和文化语境，对专业术语给出注释。"
            "输出格式：「原文」→「译文」+ 关键术语说明。回复精炼专业。"
        ),
        "keywords": "翻译 translate 英文 english 中文 chinese 日语 japanese 法语 french"
                    " 德语 german 韩语 korean 西班牙语 spanish 语言 language 文本 text",
    },
    {
        "id": "writing_assistant", "name": "写作助手", "icon": "📝",
        "mention": "@写作助手", "color": "#90b890",
        "system_prompt": (
            "我是资深文字编辑，擅长文案润色、结构优化、风格统一。"
            "优化文字时保持原意，提升可读性和感染力。"
            "输出格式：「优化后」+ 修改要点说明（3点以内）。回复精炼。"
        ),
        "keywords": "写作 write 文章 article 编辑 edit 修改 revise 润色 polish 文案 copy"
                    " 邮件 email 报告 report 总结 summary 改 优化文字 简历 演讲稿",
    },
    {
        "id": "knowledge_lecturer", "name": "知识讲师", "icon": "🎓",
        "mention": "@知识讲师", "color": "#a0b8d0",
        "system_prompt": (
            "我是资深知识讲师，擅长用通俗易懂的方式解释复杂概念。"
            "使用类比、图示描述和实例来帮助理解。"
            "回复结构：1)一句话总结 2)通俗解释 3)生活类比 4)一个简单例子。语言亲切自然。"
        ),
        "keywords": "解释 explain 什么是 what 为什么 why 如何 how 学习 learn 概念 concept"
                    " 原理 principle 教程 tutorial 入门 beginner 理解 understand 定义",
    },
    {
        "id": "creative_partner", "name": "创意伙伴", "icon": "🎨",
        "mention": "@创意伙伴", "color": "#d8a0b0",
        "system_prompt": (
            "我是创意头脑风暴伙伴，擅长产生新颖点子和跨界联想。"
            "不评判想法好坏，先发散后收敛。每个建议简洁有启发性。"
            "回复格式：3-5个创意点子（每条1-2句话），最后推荐最佳方向。"
        ),
        "keywords": "创意 idea 想法 头脑风暴 brainstorm 设计 design 命名 naming slogan"
                    " 品牌 brand 故事 story 策划 方案 创新 灵感 营销",
    },
]

# 自定义角色存储
CUSTOM_ROLES_FILE = "custom_roles.json"
CUSTOM_ROLE_COLORS = ["#d8b888", "#c8a8d8", "#a8c8c8", "#c8c8a8", "#d8a8a8",
                      "#a8b8d8", "#b8d8a8", "#d8c8a8", "#a8d8c8", "#c8a8b8"]

def load_custom_roles() -> list[dict]:
    """加载用户自定义角色"""
    return _read_json(CUSTOM_ROLES_FILE, [])

def save_custom_roles(roles: list[dict]) -> bool:
    return _write_json(CUSTOM_ROLES_FILE, roles)

def create_custom_role(name: str, icon: str, color: str, system_prompt: str, keywords: str) -> dict:
    """创建新的自定义角色"""
    rid = f"custom_{gen_id()}"
    return {
        "id": rid, "name": name, "icon": icon, "mention": f"@{name}",
        "color": color, "system_prompt": system_prompt,
        "keywords": keywords, "is_custom": True,
    }

def get_all_roles() -> list[dict]:
    """获取所有角色（预设 + 自定义）"""
    return ROLE_TEMPLATES + load_custom_roles()

MODEL_CONFIGS = {
    "deepseek-chat":      {"name": "DeepSeek-Chat",    "provider": "DeepSeek",  "env": "DEEPSEEK_API_KEY",  "url": "https://api.deepseek.com"},
    "deepseek-reasoner":  {"name": "DeepSeek-Reasoner","provider": "DeepSeek",  "env": "DEEPSEEK_API_KEY",  "url": "https://api.deepseek.com"},
    "qwen-turbo":         {"name": "Qwen-Turbo",       "provider": "阿里千问",   "env": "DASHSCOPE_API_KEY", "url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    "qwen-plus":          {"name": "Qwen-Plus",        "provider": "阿里千问",   "env": "DASHSCOPE_API_KEY", "url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    "doubao-pro-32k":     {"name": "Doubao-Pro",       "provider": "字节豆包",   "env": "DOUBAO_API_KEY",    "url": "https://ark.cn-beijing.volces.com/api/v3"},
    "glm-4":              {"name": "GLM-4",            "provider": "智谱清言",   "env": "ZHIPU_API_KEY",     "url": "https://open.bigmodel.cn/api/paas/v4"},
    "moonshot-v1-8k":     {"name": "Moonshot v1",      "provider": "月之暗面",   "env": "MOONSHOT_API_KEY",  "url": "https://api.moonshot.cn/v1"},
}

# ============================================================
# 工具函数
# ============================================================

def _ensure_dir(p: str) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def _read_json(filepath: str, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return default

def _write_json(filepath: str, data) -> bool:
    try:
        _ensure_dir(os.path.dirname(filepath))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False

def hash_password(pw: str) -> str:
    """PBKDF2-HMAC-SHA256 密码哈希（生产级单向加密）

    注意：演示项目使用 PBKDF2（10 万次迭代）。
    真正的生产环境建议升级到 bcrypt 或 argon2id，
    它们在 GPU 抗性和侧信道防护上更优。
    """
    salt = b"ai_partner_v2_salt"  # 生产环境应使用随机盐
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 100_000).hex()

def gen_id() -> str:
    return uuid.uuid4().hex[:12]

def ts_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def gen_session_name() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_role(role_id: str) -> dict | None:
    for r in get_all_roles():
        if r["id"] == role_id:
            return r
    return None

# ============================================================
# 角色匹配与 @提及
# ============================================================

def parse_mentions(message: str) -> list[str]:
    mentions = re.findall(r"@([^\s@]+)", message)
    seen, ids = set(), []
    for m in mentions:
        m = m.rstrip("，。！？、,.!?;；:：")
        for role in get_all_roles():
            if m == role["name"]:
                if role["id"] not in seen:
                    ids.append(role["id"]); seen.add(role["id"])
                break
    return ids

def match_role_keywords(message: str, candidates: list[str]) -> str | None:
    best_id, best_score = None, 0
    msg = message.lower()
    for role in get_all_roles():
        if role["id"] not in candidates or not role.get("keywords"):
            continue
        score = sum(1 for kw in role["keywords"].split() if kw.lower() in msg)
        if score > best_score:
            best_score, best_id = score, role["id"]
    return best_id

def clean_message(msg: str) -> str:
    return re.sub(r"@[^\s@]+\s*", "", msg).strip()

# ============================================================
# OpenAI 客户端
# ============================================================

def get_client(model_key: str) -> OpenAI | None:
    cfg = MODEL_CONFIGS.get(model_key)
    if not cfg:
        return None
    key = os.environ.get(cfg["env"])
    if not key:
        return None
    try:
        return OpenAI(api_key=key, base_url=cfg["url"])
    except Exception:
        return None

def get_available_models() -> dict:
    avail = {}
    for k, c in MODEL_CONFIGS.items():
        if os.environ.get(c["env"]):
            avail[k] = c
    if not avail:
        avail["deepseek-chat"] = MODEL_CONFIGS["deepseek-chat"]
    return avail

# ============================================================
# 用户管理
# ============================================================

USERS_FILE = "users/users.json"

def load_users() -> list:
    return _read_json(USERS_FILE, [])

def save_users(data: list) -> bool:
    return _write_json(USERS_FILE, data)

def find_user(uname: str) -> dict | None:
    for u in load_users():
        if u["username"] == uname:
            return u
    return None

def register_user(uname: str, pw: str) -> tuple[bool, str]:
    if not uname or not pw:
        return False, "用户名和密码不能为空"
    if len(uname) < 2:
        return False, "用户名至少2个字符"
    if len(pw) < 4:
        return False, "密码至少4个字符"
    if not re.match(r'^[\w一-龥]+$', uname):
        return False, "用户名只能包含中文、字母、数字和下划线"
    if find_user(uname):
        return False, "用户名已存在"
    users = load_users()
    users.append({
        "username": uname, "password_hash": hash_password(pw),
        "avatar": "👤", "bio": "", "created_at": ts_now(),
        "favorites": [], "liked_posts": [], "my_posts": [],
    })
    return (True, f"注册成功！欢迎 {uname}") if save_users(users) else (False, "注册失败")

def login_user(uname: str, pw: str) -> tuple[bool, str]:
    u = find_user(uname)
    if not u:
        return False, "用户不存在"
    if u["password_hash"] != hash_password(pw):
        return False, "密码错误"
    return True, f"欢迎回来，{uname}！"

# ============================================================
# 社区管理
# ============================================================

POSTS_FILE = "community/posts.json"

def load_posts() -> list:
    return _read_json(POSTS_FILE, [])

def save_posts(data: list) -> bool:
    return _write_json(POSTS_FILE, data)

def create_post(title: str, content: str, cat: str, tags: list, author: str) -> dict | None:
    if not title.strip() or not content.strip():
        return None
    post = {
        "id": gen_id(), "title": title.strip(), "content": content.strip(),
        "category": cat, "tags": [t.strip() for t in tags if t.strip()],
        "author": author, "likes": [], "favorites": [], "comments": [],
        "created_at": ts_now(),
    }
    posts = load_posts()
    posts.insert(0, post)
    if save_posts(posts):
        users = load_users()
        for u in users:
            if u["username"] == author:
                u["my_posts"].append(post["id"]); save_users(users); break
        return post
    return None

def toggle_like(pid: str, uname: str) -> bool:
    posts = load_posts()
    for p in posts:
        if p["id"] == pid:
            result = uname not in p["likes"]
            if result: p["likes"].append(uname)
            else: p["likes"].remove(uname)
            save_posts(posts)
            users = load_users()
            for u in users:
                if u["username"] == uname:
                    if result and pid not in u["liked_posts"]: u["liked_posts"].append(pid)
                    elif not result and pid in u["liked_posts"]: u["liked_posts"].remove(pid)
                    save_users(users); break
            return result
    return False

def toggle_favorite(pid: str, uname: str) -> bool:
    posts = load_posts()
    for p in posts:
        if p["id"] == pid:
            result = uname not in p["favorites"]
            if result: p["favorites"].append(uname)
            else: p["favorites"].remove(uname)
            save_posts(posts)
            users = load_users()
            for u in users:
                if u["username"] == uname:
                    if result and pid not in u["favorites"]: u["favorites"].append(pid)
                    elif not result and pid in u["favorites"]: u["favorites"].remove(pid)
                    save_users(users); break
            return result
    return False

def add_comment(pid: str, author: str, content: str) -> dict | None:
    if not content.strip():
        return None
    comment = {"id": gen_id(), "author": author, "content": content.strip(), "created_at": ts_now()}
    posts = load_posts()
    for p in posts:
        if p["id"] == pid:
            p["comments"].append(comment); save_posts(posts); return comment
    return None

def delete_post(pid: str, uname: str) -> bool:
    posts = load_posts()
    for i, p in enumerate(posts):
        if p["id"] == pid and p["author"] == uname:
            posts.pop(i); save_posts(posts)
            users = load_users()
            for u in users:
                if u["username"] == uname and pid in u["my_posts"]:
                    u["my_posts"].remove(pid); save_users(users); break
            return True
    return False

# ============================================================
# 会话持久化（per-role / group）
# ============================================================

def _session_path(name: str) -> str:
    return f"sessions/{name}.json"

def save_role_session(role_id: str) -> None:
    msgs = st.session_state.role_messages.get(role_id, [])
    if not msgs:
        return
    sn = st.session_state.role_sessions.get(role_id, gen_session_name())
    _ensure_dir("sessions")
    _write_json(_session_path(sn), {
        "type": "single", "role_id": role_id,
        "session_name": sn, "model": st.session_state.selected_model,
        "messages": msgs,
    })

def gen_group_name() -> str:
    """为新建群聊生成默认名称"""
    sessions = st.session_state.get("group_sessions", [])
    return f"群聊 {len(sessions) + 1}"

def self_save_group() -> None:
    """将当前活跃群聊保存到 group_sessions 列表（不覆盖文件）"""
    msgs = st.session_state.group_messages
    name = st.session_state.get("group_name", "")
    roles = st.session_state.group_roles
    sn = st.session_state.group_session
    if not name or not sn:
        return
    # 查找是否已存在同名会话
    sessions = st.session_state.get("group_sessions", [])
    found = False
    for s in sessions:
        if s.get("session_name") == sn:
            s["messages"] = msgs
            s["roles"] = roles
            s["name"] = name
            found = True
            break
    if not found:
        sessions.append({
            "name": name, "roles": list(roles),
            "messages": list(msgs), "session_name": sn,
        })
    st.session_state.group_sessions = sessions

def switch_group_session(idx: int) -> None:
    """切换到指定群聊会话"""
    sessions = st.session_state.get("group_sessions", [])
    if idx < 0 or idx >= len(sessions):
        return
    # 保存当前
    self_save_group()
    # 加载目标
    s = sessions[idx]
    st.session_state.group_name = s["name"]
    st.session_state.group_roles = s["roles"]
    st.session_state.group_messages = s["messages"]
    st.session_state.group_session = s["session_name"]
    st.session_state.group_setup = False
    st.session_state.active_group_idx = idx

def save_group_session() -> None:
    self_save_group()  # 同步到内存列表
    msgs = st.session_state.group_messages
    if not msgs:
        return
    sn = st.session_state.group_session or gen_session_name()
    _ensure_dir("sessions")
    _write_json(_session_path(sn), {
        "type": "group", "roles": st.session_state.group_roles,
        "session_name": sn, "model": st.session_state.selected_model,
        "messages": msgs,
    })

def list_sessions(role_id: str = None, group: bool = False) -> list[str]:
    if not os.path.exists("sessions"):
        return []
    result = []
    for fn in os.listdir("sessions"):
        if not fn.endswith(".json"):
            continue
        data = _read_json(f"sessions/{fn}")
        if not data:
            continue
        if group and data.get("type") == "group":
            result.append(fn[:-5])
        elif not group and role_id and data.get("type") == "single" and data.get("role_id") == role_id:
            result.append(fn[:-5])
        elif not group and not role_id and data.get("type") == "single":
            result.append(fn[:-5])
    return sorted(result, reverse=True)

def load_session_data(name: str) -> dict | None:
    return _read_json(_session_path(name))

def delete_session_file(name: str) -> None:
    p = _session_path(name)
    if os.path.exists(p):
        os.remove(p)

def rename_session(old_name: str, new_name: str) -> None:
    """重命名会话文件（用于自动标题更新）"""
    if old_name == new_name:
        return
    old_p = _session_path(old_name)
    new_p = _session_path(new_name)
    if os.path.exists(old_p) and not os.path.exists(new_p):
        os.rename(old_p, new_p)

def export_md(name: str) -> str | None:
    data = load_session_data(name)
    if not data:
        return None
    md = f"# 🤖 AI 角色对话记录\n\n**会话**: {name}\n\n"
    md += f"**类型**: {data.get('type','?')}\n\n**模型**: {data.get('model','?')}\n\n---\n\n"
    for m in data.get("messages", []):
        icon = "🧑" if m["role"] == "user" else "🤖"
        rn = "用户" if m["role"] == "user" else m.get("role_id", "AI")
        md += f"### {icon} {rn}\n\n{m['content']}\n\n---\n\n"
    return md

def export_json(name: str) -> str | None:
    p = _session_path(name)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

# ============================================================
# System Prompt 构建
# ============================================================

def build_role_prompt(role: dict) -> str:
    base = role.get("system_prompt", "") or "我是AI助手，请根据上下文给出专业回复。"
    return (
        f"【角色：{role['icon']} {role['name']}】\n{base}\n"
        f"重要：我是{role['name']}，严格以该角色身份回复。"
        f"回复一针见血，控制在200字以内，不要输出无关内容。"
    )

def build_brief_prompt(role: dict, user_msg: str) -> str:
    return (
        f"我是{role['icon']} {role['name']}。"
        f"请针对以下用户问题，从你的专业角度给出简短建议，"
        f"严格控制在100字以内，一针见血，不要客套。\n用户问题：{user_msg}"
    )

# ============================================================
# LLM API 调用
# ============================================================

def call_llm(client, model_id, sys_prompt, msgs, temp=0.7, top_p=1.0, stream=True):
    return client.chat.completions.create(
        model=model_id,
        messages=[{"role": "system", "content": sys_prompt}] + msgs,
        temperature=temp,
        top_p=top_p,
        stream=stream,
    )

# 全局 Token 编码器（tiktoken，OpenAI 官方库，精确计数）
_token_encoder = tiktoken.get_encoding("cl100k_base")

def estimate_tokens(text: str) -> int:
    """精确 Token 计数（基于 GPT-4/DeepSeek 共用 cl100k_base 词表）"""
    return len(_token_encoder.encode(text))

def auto_generate_title(client, model_id: str, first_message: str) -> str:
    """用 AI 生成会话标题（≤12 字），失败时返回默认值"""
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{
                "role": "user",
                "content": f"用12个汉字以内总结这段对话的主题（只输出标题，不要引号、不要解释）：\n{first_message}"
            }],
            temperature=0.3,
            max_tokens=20,
        )
        title = resp.choices[0].message.content.strip().strip('"\'《》「」')
        return title[:12] if title else None
    except Exception:
        return None

# ============================================================
# Session State 初始化
# ============================================================

def init_state():
    all_roles = get_all_roles()
    defaults = {
        # 聊天模式
        "chat_mode": "single",        # "single" | "group"
        "current_role_id": "code_reviewer",
        "role_messages": {r["id"]: [] for r in all_roles},
        "role_sessions": {r["id"]: gen_session_name() for r in all_roles},
        "group_roles": ["code_reviewer"],
        "group_messages": [],
        "group_session": gen_session_name(),
        "group_setup": True,
        "group_name": "",
        "group_sessions": [],
        "active_group_idx": 0,
        # 模型
        "selected_model": "deepseek-chat",
        "compare_model": "qwen-turbo",
        "compare_mode": False,
        "temperature": 0.7,
        "top_p": 1.0,
        # Token
        "total_in_tokens": 0,
        "total_out_tokens": 0,
        # 用户
        "logged_in": False,
        "username": None,
        "is_guest": True,
        # UI 状态
        "app_page": "chat",          # "chat" | "community" | "profile"
        "hidden_presets": [],
        "multi_role_suggest": False,
        "show_login": False,
        "login_mode": "login",
        "community_search": "",
        "community_filter": "全部",
        "viewing_post_id": None,
        "show_create_post": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # 确保新创建的自定义角色有对应的消息和会话
    for r in all_roles:
        if r["id"] not in st.session_state.role_messages:
            st.session_state.role_messages[r["id"]] = []
        if r["id"] not in st.session_state.role_sessions:
            st.session_state.role_sessions[r["id"]] = gen_session_name()

init_state()

# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="AI 角色对话平台",
    page_icon="🎆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

# ============================================================
# 顶部栏
# ============================================================

st.markdown('<div class="top-bar">', unsafe_allow_html=True)
top_left, top_right = st.columns([3, 2])
with top_left:
    st.markdown(
        '<p class="main-title" style="margin:0;">🎆 AI 角色对话平台</p>',
        unsafe_allow_html=True,
    )

with top_right:
    tc1, tc2, tc3, tc4 = st.columns([2, 1, 1, 1])
    with tc1:
        # 模型快捷切换
        avail = get_available_models()
        opts = {f"{c['name']}": k for k, c in avail.items()}
        if opts:
            cur_k = next((k for k in opts.values() if k == st.session_state.selected_model), list(opts.values())[0])
            cur_label = next((l for l, k in opts.items() if k == cur_k), list(opts.keys())[0])
            sel = st.selectbox("模型", list(opts.keys()),
                               index=list(opts.keys()).index(cur_label),
                               label_visibility="collapsed", key="top_model")
            st.session_state.selected_model = opts[sel]
    with tc2:
        if st.button("🌐 社区", key="btn_community", use_container_width=True,
                     type="primary" if st.session_state.app_page == "community" else "secondary"):
            st.session_state.app_page = "community"
            st.session_state.viewing_post_id = None
            st.rerun()
    with tc3:
        if st.session_state.logged_in:
            if st.button("👤 个人", key="btn_profile", use_container_width=True,
                         type="primary" if st.session_state.app_page == "profile" else "secondary"):
                st.session_state.app_page = "profile"
                st.rerun()
        else:
            st.button("👤 个人", key="btn_profile_disabled", use_container_width=True, disabled=True,
                      help="登录后使用")
    with tc4:
        if st.session_state.logged_in:
            if st.button("🚪 退出", key="btn_logout_top", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.is_guest = True
                st.session_state.app_page = "chat"
                st.rerun()
        else:
            if st.button("🔐 登录", key="btn_login_top", use_container_width=True):
                st.session_state.show_login = not st.session_state.show_login
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 登录对话框
# ============================================================

if st.session_state.show_login and not st.session_state.logged_in:
    with st.expander("🔐 登录 / 注册", expanded=True):
        t1, t2 = st.tabs(["登录", "注册"])
        with t1:
            with st.form("login_form"):
                st.text_input("用户名", key="li_user", placeholder="输入用户名")
                st.text_input("密码", type="password", key="li_pass", placeholder="输入密码")
                if st.form_submit_button("🔓 登录", use_container_width=True):
                    ok, msg = login_user(st.session_state.get("li_user", ""), st.session_state.get("li_pass", ""))
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.username = st.session_state.li_user
                        st.session_state.is_guest = False
                        st.session_state.show_login = False
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)
        with t2:
            with st.form("reg_form"):
                st.text_input("用户名", key="reg_user", placeholder="2-20字符")
                st.text_input("密码", type="password", key="reg_pass", placeholder="至少4字符")
                st.text_input("确认密码", type="password", key="reg_pass2", placeholder="再次输入")
                if st.form_submit_button("📝 注册", use_container_width=True):
                    if st.session_state.get("reg_pass") != st.session_state.get("reg_pass2"):
                        st.error("两次密码不一致")
                    else:
                        ok, msg = register_user(st.session_state.get("reg_user", ""), st.session_state.get("reg_pass", ""))
                        st.success(msg) if ok else st.error(msg)

# ============================================================
# 侧边栏
# ============================================================

with st.sidebar:
    # ---- 角色列表 ----
    st.markdown("### 🎭 角色选择")

    if st.session_state.chat_mode == "single":
        all_roles = get_all_roles()
        hidden = st.session_state.get("hidden_presets", [])
        # 过滤隐藏的预设角色
        visible_roles = [r for r in all_roles if not (not r.get("is_custom") and r["id"] in hidden)]
        for role in visible_roles:
            active = st.session_state.current_role_id == role["id"]
            msg_count = len(st.session_state.role_messages.get(role["id"], []))
            c1, c2 = st.columns([5, 1])
            with c1:
                is_custom = role.get("is_custom", False)
                prefix = "✨ " if is_custom else ""
                btn_label = f"{prefix}{role['icon']}  {role['name']}"
                if msg_count:
                    btn_label += f"  [{msg_count}]"
                btn_type = "primary" if active else "secondary"
                if st.button(btn_label, key=f"role_btn_{role['id']}",
                             type=btn_type, use_container_width=True):
                    if st.session_state.current_role_id != role["id"]:
                        save_role_session(st.session_state.current_role_id)
                    st.session_state.chat_mode = "single"
                    st.session_state.current_role_id = role["id"]
                    st.session_state.app_page = "chat"
                    st.rerun()
            with c2:
                if is_custom:
                    if st.button("🗑️", key=f"delcr_{role['id']}",
                                 help=f"删除「{role['name']}」", use_container_width=True):
                        custom_roles = load_custom_roles()
                        custom_roles = [r for r in custom_roles if r["id"] != role["id"]]
                        save_custom_roles(custom_roles)
                        if st.session_state.current_role_id == role["id"]:
                            st.session_state.current_role_id = "code_reviewer"
                        st.session_state.role_messages.pop(role["id"], None)
                        st.session_state.role_sessions.pop(role["id"], None)
                        st.rerun()
                else:
                    if st.button("🗑️", key=f"delpre_{role['id']}",
                                 help=f"删除「{role['name']}」", use_container_width=True):
                        if role["id"] not in hidden:
                            hidden.append(role["id"])
                            st.session_state.hidden_presets = hidden
                        if st.session_state.current_role_id == role["id"]:
                            remaining = [r for r in visible_roles if r["id"] != role["id"]]
                            st.session_state.current_role_id = remaining[0]["id"] if remaining else "code_reviewer"
                        st.rerun()

        # 恢复已删除的预设角色
        if hidden:
            st.divider()
            st.caption(f"已隐藏 {len(hidden)} 个默认角色")
            if st.button("🔄 恢复默认角色", use_container_width=True):
                st.session_state.hidden_presets = []
                st.rerun()

        # ---- 添加自定义角色 ----
        st.divider()
        if not st.session_state.get("show_create_role", False):
            if st.button("➕ 添加角色", use_container_width=True):
                st.session_state.show_create_role = True
                st.rerun()
        else:
            with st.container(border=True):
                st.markdown("**✨ 创建新角色**")
                with st.form("create_role_form"):
                    new_name = st.text_input("角色名称", placeholder="如：心理咨询师", key="cr_name")
                    new_prompt = st.text_area(
                        "角色提示词 (System Prompt)",
                        placeholder="描述角色的身份、说话风格、专业领域...\n例如：我是资深心理咨询师，擅长倾听和引导...",
                        height=150, key="cr_prompt",
                    )
                    new_keywords = st.text_input(
                        "关键词（空格分隔）",
                        placeholder="心理 情绪 焦虑 压力 咨询 倾听",
                        key="cr_keywords",
                    )
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.form_submit_button("✅ 创建", use_container_width=True):
                            if not new_name.strip():
                                st.error("请输入角色名称")
                            elif not new_prompt.strip():
                                st.error("请输入角色提示词")
                            else:
                                # 自动分配图标和颜色（基于名称哈希）
                                auto_icons = ["🤖", "🧠", "💡", "🦊", "🐱", "🌟", "🔮", "🎯", "💎", "🔥"]
                                auto_color = CUSTOM_ROLE_COLORS[hash(new_name) % len(CUSTOM_ROLE_COLORS)]
                                auto_icon = auto_icons[hash(new_name) % len(auto_icons)]
                                role = create_custom_role(
                                    new_name.strip(), auto_icon,
                                    auto_color, new_prompt.strip(), new_keywords.strip(),
                                )
                                custom_roles = load_custom_roles()
                                custom_roles.append(role)
                                save_custom_roles(custom_roles)
                                st.session_state.role_messages[role["id"]] = []
                                st.session_state.role_sessions[role["id"]] = gen_session_name()
                                st.session_state.current_role_id = role["id"]
                                st.session_state.chat_mode = "single"
                                st.session_state.show_create_role = False
                                st.success(f"角色「{role['name']}」创建成功！")
                                st.rerun()
                    with c_btn2:
                        if st.form_submit_button("❌ 取消", use_container_width=True):
                            st.session_state.show_create_role = False
                            st.rerun()

        # 群聊入口
        st.divider()
        if st.button("👥 进入群聊模式", use_container_width=True, type="primary"):
            save_role_session(st.session_state.current_role_id)
            st.session_state.chat_mode = "group"
            st.session_state.app_page = "chat"
            # 已有保存的群聊 → 直接进入；否则 → 创建新群聊
            sessions = st.session_state.get("group_sessions", [])
            if sessions:
                s = sessions[-1]  # 最近一个
                st.session_state.group_name = s["name"]
                st.session_state.group_roles = s["roles"]
                st.session_state.group_messages = s["messages"]
                st.session_state.group_session = s["session_name"]
                st.session_state.group_setup = False
                st.session_state.active_group_idx = len(sessions) - 1
            else:
                st.session_state.group_setup = True
            st.rerun()

    else:
        # 群聊模式
        if st.session_state.get("group_setup", True):
            # ── 群聊创建阶段：勾选角色 ──
            st.caption("勾选参与群聊的角色：")
            new_roles = []
            hidden = st.session_state.get("hidden_presets", [])
            for role in get_all_roles():
                if not role.get("is_custom") and role["id"] in hidden:
                    continue
                chk = st.checkbox(
                    f"{role['icon']} {role['name']}",
                    value=role["id"] in st.session_state.group_roles,
                    key=f"grp_{role['id']}",
                )
                if chk:
                    new_roles.append(role["id"])
            st.session_state.group_roles = new_roles

            st.divider()
            if st.button("✅ 确认创建群聊", use_container_width=True, type="primary",
                         disabled=len(new_roles) < 1):
                st.session_state.group_roles = new_roles
                st.session_state.group_name = gen_group_name()
                st.session_state.group_messages = []
                st.session_state.group_session = gen_session_name()
                st.session_state.group_setup = False
                st.rerun()

            if st.button("🔙 返回单人模式", use_container_width=True):
                st.session_state.chat_mode = "single"
                st.session_state.group_setup = True
                st.session_state.app_page = "chat"
                st.rerun()
        else:
            # ── 群聊活跃阶段：新建+保存 | 返回+名称 ──
            col_a, col_b, col_c = st.columns([1, 1, 2])
            with col_a:
                if st.button("📝", key="new_group_side", help="新建群聊", use_container_width=True):
                    self_save_group()
                    st.session_state.group_messages = []
                    st.session_state.group_roles = ["code_reviewer"]
                    st.session_state.group_name = gen_group_name()
                    st.session_state.group_session = gen_session_name()
                    st.session_state.group_setup = True
                    st.rerun()
            with col_b:
                if st.button("💾", key="save_group_side", help="保存群聊记录", use_container_width=True):
                    self_save_group()
                    save_group_session()
                    st.toast("群聊已保存", icon="✅")
            col_r1, col_r2 = st.columns([1, 3])
            with col_r1:
                if st.button("🔙", key="back_single_side", help="返回单人模式", use_container_width=True):
                    self_save_group()
                    st.session_state.chat_mode = "single"
                    st.session_state.group_setup = True
                    st.session_state.app_page = "chat"
                    st.rerun()
            with col_r2:
                new_name = st.text_input(
                    "群聊名称", value=st.session_state.get("group_name", ""),
                    key="group_name_edit", label_visibility="collapsed",
                    placeholder="群聊名称",
                )
                if new_name != st.session_state.get("group_name", ""):
                    st.session_state.group_name = new_name.strip() or "未命名群聊"

    st.divider()

    # ---- 模型参数 ----
    if st.session_state.chat_mode == "group" and not st.session_state.get("group_setup", True):
        st.markdown(f"### 🧠 模型参数 · {st.session_state.get('group_name', '群聊')}")
    else:
        st.markdown("### 🧠 模型参数")
    model_cfg = MODEL_CONFIGS.get(st.session_state.selected_model, {})
    st.caption(f"当前：{model_cfg.get('name','?')} ({model_cfg.get('provider','?')})")

    # 模型选择
    avail_dict = get_available_models()
    model_labels = {f"{c['name']}": k for k, c in avail_dict.items()}
    # 也包含未配置的模型
    all_labels = {}
    for k, c in MODEL_CONFIGS.items():
        prefix = "🟢 " if k in avail_dict else "🔒 "
        all_labels[f"{prefix}{c['name']} ({c['provider']})"] = k
    cur_label = next((l for l, k in all_labels.items() if k == st.session_state.selected_model), list(all_labels.keys())[0])
    sel_model = st.selectbox("切换模型", list(all_labels.keys()),
                             index=list(all_labels.keys()).index(cur_label),
                             key="sidebar_model")
    st.session_state.selected_model = all_labels[sel_model]

    # 模型对比模式（仅单人模式）
    if st.session_state.chat_mode == "single":
        st.divider()
        st.session_state.compare_mode = st.toggle(
            "🔬 模型对比",
            value=st.session_state.compare_mode,
            help="同时用两个模型回答同一问题，并排对比"
        )
        if st.session_state.compare_mode:
            compare_labels = {l: k for l, k in all_labels.items()
                            if k != st.session_state.selected_model}
            if compare_labels:
                cur_comp = next(
                    (l for l, k in compare_labels.items()
                     if k == st.session_state.compare_model),
                    list(compare_labels.keys())[0]
                )
                sel_comp = st.selectbox(
                    "对比模型", list(compare_labels.keys()),
                    index=list(compare_labels.keys()).index(cur_comp),
                    key="sidebar_compare"
                )
                st.session_state.compare_model = compare_labels[sel_comp]
            else:
                st.caption("⚠️ 请先配置多个模型的 API Key")
        st.divider()

    # 创意程度：统一为直观的滑块
    st.markdown("**🎨 创意程度**")
    creativity_labels = ["🔒 严谨精确", "📏 比较严谨", "⚖️ 均衡适中", "💡 有点创意", "🎨 天马行空"]
    creativity_map = {
        "🔒 严谨精确": (0.1, 0.85),
        "📏 比较严谨": (0.4, 0.90),
        "⚖️ 均衡适中": (0.8, 0.95),
        "💡 有点创意": (1.2, 0.98),
        "🎨 天马行空": (1.7, 1.0),
    }
    # 找出当前值对应的标签
    current_creativity = "⚖️ 均衡适中"
    for label, (t, p) in creativity_map.items():
        if abs(st.session_state.temperature - t) < 0.15:
            current_creativity = label
            break
    selected_creativity = st.select_slider(
        "回复风格",
        options=creativity_labels,
        value=current_creativity,
        help="控制AI回复的创造性：从严谨精准到天马行空",
    )
    st.session_state.temperature, st.session_state.top_p = creativity_map[selected_creativity]

    st.divider()

    # ---- 群聊会话管理（仅群聊活跃阶段） ----
    if st.session_state.chat_mode == "group" and not st.session_state.get("group_setup", True):
        st.markdown("### 📋 群聊会话")
        sessions = st.session_state.get("group_sessions", [])
        if sessions:
            for i, s in enumerate(sessions):
                c1, c2 = st.columns([4, 1])
                with c1:
                    active = (i == st.session_state.get("active_group_idx", 0) and
                              s.get("session_name") == st.session_state.group_session)
                    btn_type = "primary" if active else "secondary"
                    msg_n = len(s.get("messages", []))
                    label = f"{s.get('name','?')} [{msg_n}]"
                    if st.button(label, key=f"swgrp_{i}", type=btn_type, use_container_width=True):
                        switch_group_session(i)
                        st.rerun()
                with c2:
                    if st.button("✕", key=f"delgrp_{i}", use_container_width=True,
                                 help=f"删除「{s.get('name','')}」"):
                        sessions.pop(i)
                        st.session_state.group_sessions = sessions
                        if st.session_state.active_group_idx >= len(sessions):
                            st.session_state.active_group_idx = max(0, len(sessions) - 1)
                        st.rerun()
        else:
            st.caption("暂无已保存的群聊")

    st.divider()

    # ---- 多角色建议（仅群聊） ----
    if st.session_state.chat_mode == "group":
        st.session_state.multi_role_suggest = st.toggle(
            "🗣️ 多角色建议",
            value=st.session_state.multi_role_suggest,
            help="开启后其他活跃角色也给出≤100字简短建议",
        )
        st.divider()

    # ---- 会话管理 ----
    st.markdown("### 💬 会话管理")

    if st.session_state.chat_mode == "single":
        rid = st.session_state.current_role_id
        role = get_role(rid)
        if role:
            st.caption(f"当前角色：{role['icon']} {role['name']}")

        if st.button("📝 新建会话", key="new_single_session", use_container_width=True):
            save_role_session(rid)
            st.session_state.role_messages[rid] = []
            st.session_state.role_sessions[rid] = gen_session_name()
            st.rerun()

        # 历史会话
        sessions = list_sessions(role_id=rid)
        if sessions:
            st.caption(f"历史会话 ({len(sessions)})")
            for s in sessions[:8]:
                c1, c2 = st.columns([4, 1])
                with c1:
                    active = s == st.session_state.role_sessions.get(rid, "")
                    btn_type = "primary" if active else "secondary"
                    if st.button(s, key=f"load_{s}", type=btn_type, use_container_width=True):
                        data = load_session_data(s)
                        if data:
                            st.session_state.role_messages[rid] = data.get("messages", [])
                            st.session_state.role_sessions[rid] = s
                            st.rerun()
                with c2:
                    if st.button("🗑️", key=f"del_{s}", use_container_width=True):
                        delete_session_file(s)
                        if s == st.session_state.role_sessions.get(rid, ""):
                            st.session_state.role_messages[rid] = []
                            st.session_state.role_sessions[rid] = gen_session_name()
                        st.rerun()
        else:
            st.caption("暂无历史会话")
    else:
        # 群聊会话
        st.caption(f"群聊角色：{', '.join(get_role(r)['name'] for r in st.session_state.group_roles if get_role(r))}")
        sessions = list_sessions(group=True)
        if sessions:
            st.caption(f"群聊历史 ({len(sessions)})")
            for s in sessions[:8]:
                c1, c2 = st.columns([4, 1])
                with c1:
                    active = s == st.session_state.group_session
                    btn_type = "primary" if active else "secondary"
                    if st.button(s, key=f"loadg_{s}", type=btn_type, use_container_width=True):
                        data = load_session_data(s)
                        if data:
                            st.session_state.group_messages = data.get("messages", [])
                            st.session_state.group_roles = data.get("roles", ["code_reviewer"])
                            st.session_state.group_session = s
                            st.rerun()
                with c2:
                    if st.button("🗑️", key=f"delg_{s}", use_container_width=True):
                        delete_session_file(s)
                        if s == st.session_state.group_session:
                            st.session_state.group_messages = []
                            st.session_state.group_session = gen_session_name()
                        st.rerun()
        else:
            st.caption("暂无群聊历史")

    st.divider()

    # ---- Token（可折叠）----
    total = st.session_state.total_in_tokens + st.session_state.total_out_tokens
    with st.expander(f"📊 Token 用量 · {total:,}", expanded=False):
        c1, c2 = st.columns(2)
        with c1: st.metric("📥 输入", f"{st.session_state.total_in_tokens:,}")
        with c2: st.metric("📤 输出", f"{st.session_state.total_out_tokens:,}")

    st.divider()

    # ---- 导出 ----
    st.markdown("### 📤 导出")
    cur_sn = st.session_state.role_sessions.get(st.session_state.current_role_id, "") if st.session_state.chat_mode == "single" else st.session_state.group_session
    md = export_md(cur_sn)
    if md:
        st.download_button("📝 Markdown", md, f"{cur_sn}.md", "text/markdown", use_container_width=True)
    js = export_json(cur_sn)
    if js:
        st.download_button("📋 JSON", js, f"{cur_sn}.json", "application/json", use_container_width=True)

# ============================================================
# 主内容区路由
# ============================================================

if st.session_state.app_page == "community":
    # ==================== 社区广场 ====================
    st.markdown("### 🌐 社区广场")
    st.caption("分享角色模板、提示词优化技巧")

    is_login = st.session_state.logged_in and not st.session_state.is_guest
    cs, cf, cc = st.columns([3, 2, 1])
    with cs:
        sq = st.text_input("🔍 搜索", placeholder="搜索帖子...", key="comm_search", label_visibility="collapsed")
    with cf:
        cat_f = st.selectbox("分类", ["全部", "角色模板", "提示词优化", "使用技巧", "其他"], key="comm_cat", label_visibility="collapsed")
    with cc:
        if is_login:
            if st.button("✏️ 发帖", use_container_width=True, type="primary"):
                st.session_state.show_create_post = True
        else:
            st.button("🔒 发帖", use_container_width=True, disabled=True)

    st.divider()

    # 创建帖子
    if is_login and st.session_state.show_create_post:
        with st.expander("✏️ 发布新帖", expanded=True):
            with st.form("create_post_f"):
                pt = st.text_input("标题", placeholder="起个吸引人的标题...")
                pc = st.text_area("内容", placeholder="分享你的角色模板、提示词优化...", height=180)
                c1, c2 = st.columns(2)
                with c1: pcat = st.selectbox("分类", ["角色模板", "提示词优化", "使用技巧", "其他"])
                with c2: tags_in = st.text_input("标签（逗号分隔）", placeholder="代码审查, 效率")
                if st.form_submit_button("📤 发布", use_container_width=True):
                    tags = [t.strip() for t in tags_in.split(",") if t.strip()]
                    post = create_post(pt, pc, pcat, tags, st.session_state.username)
                    if post:
                        st.success("发布成功！"); st.session_state.show_create_post = False; st.rerun()
                    else:
                        st.error("标题和内容不能为空")

    posts = load_posts()
    if sq:
        q = sq.lower()
        posts = [p for p in posts if q in p["title"].lower() or q in p.get("content","").lower() or any(q in t.lower() for t in p.get("tags",[]))]
    if cat_f != "全部":
        posts = [p for p in posts if p.get("category") == cat_f]

    if not posts:
        st.info("暂无帖子 🚀")
    elif st.session_state.viewing_post_id:
        post = next((p for p in posts if p["id"] == st.session_state.viewing_post_id), None)
        if post:
            if st.button("← 返回列表"):
                st.session_state.viewing_post_id = None; st.rerun()
            st.markdown(f"### {post['title']}")
            st.caption(f"👤 {post['author']} · 🕐 {post['created_at']} · 📂 {post.get('category','')}")
            if post.get("tags"):
                st.markdown(" ".join([f'<span class="role-chip">#{t}</span>' for t in post["tags"]]), unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(post["content"])
            st.markdown("---")
            c1, c2, c3 = st.columns([1, 1, 4])
            liked = is_login and st.session_state.username in post.get("likes", [])
            faved = is_login and st.session_state.username in post.get("favorites", [])
            with c1:
                if st.button(f"{'❤️' if liked else '🤍'} {len(post.get('likes',[]))}", key=f"like_{post['id']}", disabled=not is_login):
                    toggle_like(post["id"], st.session_state.username); st.rerun()
            with c2:
                if st.button(f"{'⭐' if faved else '☆'} {len(post.get('favorites',[]))}", key=f"fav_{post['id']}", disabled=not is_login):
                    toggle_favorite(post["id"], st.session_state.username); st.rerun()
            with c3:
                if is_login and st.session_state.username == post["author"]:
                    if st.button("🗑️ 删除", key=f"delp_{post['id']}"):
                        delete_post(post["id"], st.session_state.username)
                        st.session_state.viewing_post_id = None; st.rerun()
            st.markdown("#### 💬 评论")
            for cmt in post.get("comments", []):
                with st.container(border=True):
                    st.markdown(f"**{cmt['author']}** · *{cmt['created_at']}*")
                    st.markdown(f"<small>{cmt['content']}</small>", unsafe_allow_html=True)
            if is_login:
                with st.form(f"cmt_{post['id']}"):
                    ct = st.text_area("评论", placeholder="写下你的想法...", key=f"cmt_in_{post['id']}")
                    if st.form_submit_button("💬 发表", clear_on_submit=True):
                        if add_comment(post["id"], st.session_state.username, ct):
                            st.success("已发表"); st.rerun()
            else:
                st.caption("🔒 登录后可评论")
    else:
        for post in posts:
            st.markdown(f'<div class="post-card">', unsafe_allow_html=True)
            cm, cs2 = st.columns([5, 1])
            with cm:
                st.markdown(f"#### {post['title']}")
                st.caption(f"👤 {post['author']} · 🕐 {post['created_at']} · 📂 {post.get('category','')}")
                preview = post["content"][:100].replace("\n", " ")
                if len(post["content"]) > 100: preview += "..."
                st.caption(preview)
                if post.get("tags"):
                    st.markdown(" ".join([f'<span class="role-chip" style="font-size:10px;padding:2px 8px;">#{t}</span>' for t in post["tags"]]), unsafe_allow_html=True)
            with cs2:
                st.metric("❤️", len(post.get("likes",[])))
                st.metric("💬", len(post.get("comments",[])))
            if st.button("查看详情 →", key=f"v_{post['id']}", use_container_width=True):
                st.session_state.viewing_post_id = post["id"]; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.app_page == "profile":
    # ==================== 个人中心 ====================
    if not st.session_state.logged_in:
        st.warning("请先登录")
    else:
        uname = st.session_state.username
        user = find_user(uname)
        st.markdown(f"### 👤 {uname} 的个人中心")
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        ca, ci = st.columns([1, 4])
        with ca:
            st.markdown(f"<div style='font-size:3.5rem;text-align:center;'>{user.get('avatar','👤') if user else '👤'}</div>", unsafe_allow_html=True)
        with ci:
            st.markdown(f"**用户名**: {uname}")
            st.markdown(f"**注册时间**: {user.get('created_at','?') if user else '?'}")
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("📝 帖子", len(user.get("my_posts",[])) if user else 0)
        with c2: st.metric("❤️ 点赞", len(user.get("liked_posts",[])) if user else 0)
        with c3: st.metric("⭐ 收藏", len(user.get("favorites",[])) if user else 0)

        t1, t2, t3 = st.tabs(["📝 我的帖子", "⭐ 我的收藏", "❤️ 我的点赞"])
        all_posts = load_posts()
        with t1:
            mp = [p for p in all_posts if p["id"] in (user.get("my_posts",[]) if user else [])]
            if not mp: st.caption("暂无帖子")
            else:
                for p in mp:
                    with st.container(border=True):
                        st.markdown(f"**{p['title']}**")
                        st.caption(f"🕐 {p['created_at']} · ❤️{len(p.get('likes',[]))} · 💬{len(p.get('comments',[]))}")
        with t2:
            fp = [p for p in all_posts if p["id"] in (user.get("favorites",[]) if user else [])]
            if not fp: st.caption("暂无收藏")
            else:
                for p in fp:
                    with st.container(border=True):
                        st.markdown(f"**{p['title']}** · 👤 {p['author']}")
        with t3:
            lp = [p for p in all_posts if p["id"] in (user.get("liked_posts",[]) if user else [])]
            if not lp: st.caption("暂无点赞")
            else:
                for p in lp:
                    with st.container(border=True):
                        st.markdown(f"**{p['title']}** · 👤 {p['author']}")

else:
    # ==================== AI 对话（默认页面）====================
    if st.session_state.chat_mode == "single":
        # ---- 单人模式 ----
        rid = st.session_state.current_role_id
        role = get_role(rid)
        if not role:
            st.error("角色不存在")
        else:
            # 头部信息
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
                f'<span style="font-size:2rem;">{role["icon"]}</span>'
                f'<span style="font-size:1.2rem;font-weight:600;color:{role["color"]};">{role["name"]}</span>'
                f'<span style="color:#6b8299;font-size:13px;">— {role["mention"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"📌 会话：{st.session_state.role_sessions.get(rid, '?')}")

            # 消息历史 -- 淡入容器
            # 时间戳 + 装饰微点
            st.markdown(
                f'<div class="chat-fade-in" data-ts="{datetime.now().timestamp()}">'
                f'<div class="deco-dot deco-dot-1"></div>'
                f'<div class="deco-dot deco-dot-2"></div>'
                f'<div class="deco-dot deco-dot-3"></div>',
                unsafe_allow_html=True,
            )
            messages = st.session_state.role_messages.get(rid, [])
            for msg in messages:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar=role["icon"]):
                        st.write(msg["content"])

            # 欢迎提示
            if not messages:
                with st.chat_message("assistant", avatar=role["icon"]):
                    color = role["color"]
                    st.markdown(f"""
                    <div style="color:#b0bec5;">
                    我是 <b style="color:{color};">{role['icon']} {role['name']}</b>。<br>
                    {role['system_prompt'][:120]}...<br><br>
                    直接输入问题开始对话，或切换到其他角色。
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
            # 聊天输入
            compare_on = st.session_state.compare_mode
            prompt = st.chat_input(f"与 {role['name']} 对话..."
                                  + (" [对比模式]" if compare_on else ""))
            if prompt:
                st.chat_message("user").write(prompt)
                messages.append({"role": "user", "content": prompt})
                sys_p = build_role_prompt(role)
                api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]] + [{"role": "user", "content": prompt}]

                client = get_client(st.session_state.selected_model)
                if client is None:
                    st.error(f"模型 `{st.session_state.selected_model}` 的 API Key 未配置。")

                elif compare_on:
                    # ── 模型对比模式（并行调用）──
                    client2 = get_client(st.session_state.compare_model)
                    if client2 is None:
                        st.error(f"对比模型 `{st.session_state.compare_model}` 的 API Key 未配置。")
                    else:
                        m1_cfg = MODEL_CONFIGS[st.session_state.selected_model]
                        m2_cfg = MODEL_CONFIGS[st.session_state.compare_model]
                        col1, col2 = st.columns(2)

                        with col1:
                            st.caption(f"🔵 {m1_cfg['name']} ({m1_cfg['provider']})")
                            ph1 = st.empty()
                        with col2:
                            st.caption(f"🟣 {m2_cfg['name']} ({m2_cfg['provider']})")
                            ph2 = st.empty()

                        # 定义线程任务
                        def _stream_col(client, model_id, placeholder):
                            full = ""
                            try:
                                resp = call_llm(client, model_id, sys_p, api_msgs,
                                               st.session_state.temperature, st.session_state.top_p)
                                for chunk in resp:
                                    if chunk.choices[0].delta.content is not None:
                                        full += chunk.choices[0].delta.content
                                return (full, None)
                            except Exception as e:
                                return (full, str(e))

                        results = {}
                        with ThreadPoolExecutor(max_workers=2) as pool:
                            futures = {
                                pool.submit(_stream_col, client, st.session_state.selected_model, ph1): "m1",
                                pool.submit(_stream_col, client2, st.session_state.compare_model, ph2): "m2",
                            }
                            for fut in as_completed(futures):
                                results[futures[fut]] = fut.result()

                        full1, err1 = results.get("m1", ("", "未返回"))
                        full2, err2 = results.get("m2", ("", "未返回"))

                        if err1:
                            col1.error(f"调用失败：{err1}")
                        else:
                            col1.markdown(full1)

                        if err2:
                            col2.error(f"调用失败：{err2}")
                        else:
                            col2.markdown(full2)

                        combined = (
                            f"**[{m1_cfg['name']}]**\n{full1}\n\n"
                            f"---\n\n"
                            f"**[{m2_cfg['name']}]**\n{full2}"
                        )
                        messages.append({"role": "assistant", "content": combined, "role_id": rid})
                        st.session_state.total_in_tokens += estimate_tokens(sys_p + prompt) * 2
                        st.session_state.total_out_tokens += estimate_tokens(full1 + full2)

                        if len(messages) == 2:
                            title = auto_generate_title(client, st.session_state.selected_model, prompt)
                            if title:
                                old_name = st.session_state.role_sessions[rid]
                                st.session_state.role_sessions[rid] = title
                                rename_session(old_name, title)

                else:
                    # ── 普通单人模式 ──
                    try:
                        with st.chat_message("assistant", avatar=role["icon"]):
                            ph = st.empty()
                            full = ""
                            resp = call_llm(client, st.session_state.selected_model,
                                           sys_p, api_msgs,
                                           st.session_state.temperature, st.session_state.top_p)
                            for chunk in resp:
                                if chunk.choices[0].delta.content is not None:
                                    full += chunk.choices[0].delta.content
                                    ph.markdown(full + "▌")
                            ph.markdown(full)
                        messages.append({"role": "assistant", "content": full, "role_id": rid})
                        st.session_state.total_in_tokens += estimate_tokens(sys_p + prompt)
                        st.session_state.total_out_tokens += estimate_tokens(full)

                        if len(messages) == 2:
                            title = auto_generate_title(client, st.session_state.selected_model, prompt)
                            if title:
                                old_name = st.session_state.role_sessions[rid]
                                st.session_state.role_sessions[rid] = title
                                rename_session(old_name, title)
                    except Exception as e:
                        st.error(f"调用失败：{e}")

                st.session_state.role_messages[rid] = messages
                save_role_session(rid)
                st.rerun()

    else:
        # ---- 群聊模式 ----
        if st.session_state.get("group_setup", True):
            # 群聊创建阶段：提示用户在侧边栏设置
            st.info("👥 请在左侧边栏勾选参与群聊的角色，输入群聊名称，然后点击「确认创建群聊」")
        else:
            gname = st.session_state.get("group_name", "群聊")
            st.markdown(f"### 👥 {gname}")

        if not st.session_state.get("group_setup", True):
            group_roles_data = [get_role(r) for r in st.session_state.group_roles if get_role(r)]
            chips = " ".join([
                f'<span class="role-chip" style="border-color:{r["color"]}40;color:{r["color"]};">'
                f'{r["icon"]} {r["mention"]}</span>'
                for r in group_roles_data
            ])
            st.markdown(
                f'<div style="margin-bottom:8px;">'
                f'<span style="color:#7890a0;font-size:13px;">群聊成员：</span>{chips}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"📌 会话：{st.session_state.group_session}")

            # 消息历史 -- 淡入容器
            st.markdown(
            f'<div class="chat-fade-in" data-ts="{datetime.now().timestamp()}">'
            f'<div class="deco-dot deco-dot-1"></div>'
            f'<div class="deco-dot deco-dot-2"></div>'
            f'<div class="deco-dot deco-dot-3"></div>',
            unsafe_allow_html=True,
        )
        for msg in st.session_state.group_messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                role_d = get_role(msg.get("role_id", ""))
                av = role_d["icon"] if role_d else "🤖"
                nm = role_d["name"] if role_d else "AI"
                with st.chat_message("assistant", avatar=av):
                    st.caption(f"🎭 {nm}")
                    st.write(msg["content"])

        # 欢迎
        if not st.session_state.group_messages:
            with st.chat_message("assistant", avatar="👥"):
                st.markdown("""
                ### 欢迎进入群聊模式 👥
                在群聊中，你可以同时与多位 AI 角色对话：
                - 使用 `@角色名` 指定某个角色回复
                - 不 @ 则自动匹配最相关的角色
                - 开启「多角色建议」可同时获得多个视角
                """)

        st.markdown('</div>', unsafe_allow_html=True)
        # 输入
        prompt = st.chat_input("群聊中... 使用 @角色名 指定回复角色")
        if prompt:
            mentioned = parse_mentions(prompt)
            clean_p = clean_message(prompt)

            if not clean_p and not mentioned:
                st.warning("请输入有效消息")
                st.stop()

            # 确定主角色
            if mentioned:
                pid = None
                for m in mentioned:
                    if m in st.session_state.group_roles:
                        pid = m; break
                if not pid:
                    pid = st.session_state.group_roles[0]
            else:
                matched = match_role_keywords(prompt, st.session_state.group_roles)
                pid = matched or st.session_state.group_roles[0]

            prole = get_role(pid)
            if not prole:
                st.error("角色异常"); st.stop()

            st.chat_message("user").write(prompt)
            st.session_state.group_messages.append({"role": "user", "content": prompt, "target_role": pid})

            client = get_client(st.session_state.selected_model)
            if client is None:
                st.error(f"模型 `{st.session_state.selected_model}` 的 API Key 未配置。")
                st.stop()

            sys_p = build_role_prompt(prole)
            api_msgs = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.group_messages[:-1]
                if m.get("role_id", "") == pid or m["role"] == "user"
            ] + [{"role": "user", "content": clean_p or prompt}]

            try:
                with st.chat_message("assistant", avatar=prole["icon"]):
                    st.caption(f"🎭 {prole['name']}")
                    ph = st.empty(); full = ""
                    resp = call_llm(client, st.session_state.selected_model,
                                   sys_p, api_msgs,
                                   st.session_state.temperature, st.session_state.top_p)
                    for chunk in resp:
                        if chunk.choices[0].delta.content is not None:
                            full += chunk.choices[0].delta.content
                            ph.markdown(full + "▌")
                    ph.markdown(full)
                st.session_state.group_messages.append({"role": "assistant", "content": full, "role_id": pid, "is_primary": True})
                st.session_state.total_in_tokens += estimate_tokens(sys_p + (clean_p or prompt))
                st.session_state.total_out_tokens += estimate_tokens(full)
            except Exception as e:
                st.error(f"调用失败：{e}")

            # 多角色建议
            if st.session_state.multi_role_suggest:
                others = [r for r in group_roles_data if r["id"] != pid]
                if others:
                    st.markdown("---")
                    st.caption("💡 其他角色建议：")
                    cols = st.columns(min(len(others), 3))
                    for i, r in enumerate(others):
                        with cols[i % 3]:
                            with st.container(border=True):
                                st.markdown(f"**{r['icon']} {r['name']}**")
                                try:
                                    bp = build_brief_prompt(r, clean_p or prompt)
                                    br = call_llm(client, st.session_state.selected_model,
                                                 bp, [{"role": "user", "content": clean_p or prompt}],
                                                 st.session_state.temperature, st.session_state.top_p)
                                    bt = ""; ph2 = st.empty()
                                    for chunk in br:
                                        if chunk.choices[0].delta.content is not None:
                                            bt += chunk.choices[0].delta.content
                                            if len(bt) <= 120:
                                                ph2.markdown(f"<small>{bt}▌</small>", unsafe_allow_html=True)
                                    if len(bt) > 120: bt = bt[:100] + "..."
                                    ph2.markdown(f"<small>{bt}</small>", unsafe_allow_html=True)
                                    st.session_state.group_messages.append({"role": "assistant", "content": bt, "role_id": r["id"], "is_primary": False})
                                    st.session_state.total_out_tokens += estimate_tokens(bt)
                                except Exception:
                                    st.caption("⚠️ 获取失败")

            save_group_session()
            st.rerun()

# ============================================================
# 页脚
# ============================================================

st.markdown("---")
st.caption(
    "🎆 AI 角色对话平台 | Powered by DeepSeek · 千问 · 豆包 · 智谱 · Moonshot | "
    "游客可免费对话 · 登录解锁社区功能"
)
