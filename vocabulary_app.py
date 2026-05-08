#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern Vocabulary & Notes Manager
Supabase ile bağlantılı, masaüstünden çift tıklanarak çalışan uygulamadır.
SSL doğrulaması kapalı, Supabase bilgileri kod içerisinde.
"""

import os
import sys
import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import requests
import urllib3

# ⚠️ SSL doğrulamasını kapatıyoruz (geliştirme için)
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ==============================================================================
# ⚙️ SUPABASE BİLGİLERİNİ BURAYA YAZ
# ==============================================================================

# 👇 BURAYA KENDI BİLGİLERİNİ YAZ
SUPABASE_URL = "https://fwjcvniqkjytznykvruj.supabase.co"  # URL'ni buraya yaz
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3amN2bmlxa2p5dHpueWt2cnVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc4ODQ5NDcsImV4cCI6MjA5MzQ2MDk0N30.HV7JS9NzYRhoB8bZ0NTiUiU_Lz4Hgyf0WKml3DhPuUk"  # Key'i buraya yaz
# 👆 BURAYA KENDI BİLGİLERİNİ YAZ

# ==============================================================================

app = Flask(__name__)
CORS(app)

# ==============================================================================
# SUPABASE API HELPERLERİ
# ==============================================================================

class SupabaseAPI:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            'apikey': key,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}'
        }
    
    def select(self, table: str, query: str = '*'):
        """Veri çek"""
        try:
            response = requests.get(
                f'{self.url}/rest/v1/{table}?select={query}&order=created_at.desc',
                headers=self.headers,
                timeout=5,
                verify=False  # ✅ SSL doğrulaması kapalı
            )
            if response.status_code == 200:
                return True, response.json()
            return False, f'Hata {response.status_code}'
        except Exception as e:
            return False, str(e)
    
    def insert(self, table: str, data: dict):
        """Veri ekle"""
        try:
            response = requests.post(
                f'{self.url}/rest/v1/{table}',
                headers=self.headers,
                json=data,
                timeout=5,
                verify=False  # ✅ SSL doğrulaması kapalı
            )
            if response.status_code == 201:
                return True, response.json()
            else:
                # Hata detayları
                print(f"❌ POST {table} - Status: {response.status_code}")
                print(f"   Yanıt: {response.text}")
                return False, f'Hata {response.status_code}: {response.text}'
        except Exception as e:
            print(f"❌ Exception in insert: {str(e)}")
            return False, str(e)
    
    def delete(self, table: str, id: int):
        """Veri sil"""
        try:
            response = requests.delete(
                f'{self.url}/rest/v1/{table}?id=eq.{id}',
                headers=self.headers,
                timeout=5,
                verify=False  # ✅ SSL doğrulaması kapalı
            )
            if response.status_code == 204:
                return True, None
            return False, f'Hata {response.status_code}'
        except Exception as e:
            return False, str(e)

def get_supabase() -> SupabaseAPI:
    return SupabaseAPI(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# FLASK ROUTES
# ==============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocabulary Manager - Modern Edition</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* HEADER */
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 25px 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 28px;
            color: #333;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        .header-buttons {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }

        .btn-secondary:hover {
            background: #e0e0e0;
        }

        /* MAIN CONTENT */
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            flex: 1;
            overflow: hidden;
        }

        /* LEFT PANEL - FORM */
        .panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            gap: 20px;
            backdrop-filter: blur(10px);
            overflow-y: auto;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-group label {
            font-size: 13px;
            font-weight: 600;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-group input,
        .form-group textarea {
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group textarea {
            resize: vertical;
            min-height: 100px;
            font-family: 'Segoe UI', monospace;
        }

        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }

        .form-actions .btn {
            flex: 1;
        }

        /* TABS */
        .tabs {
            display: flex;
            gap: 10px;
            border-bottom: 2px solid #e0e0e0;
        }

        .tab {
            padding: 12px 20px;
            border: none;
            background: none;
            cursor: pointer;
            font-weight: 600;
            color: #999;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            font-size: 14px;
        }

        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .tab:hover {
            color: #555;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* RIGHT PANEL - DATAGRID */
        .right-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow: hidden;
        }

        .data-grid {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            flex: 1;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(10px);
        }

        .data-grid h3 {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }

        .table-wrapper {
            flex: 1;
            overflow: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        thead {
            position: sticky;
            top: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            z-index: 10;
        }

        th {
            padding: 14px;
            text-align: left;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        td {
            padding: 12px 14px;
            border-bottom: 1px solid #f0f0f0;
            color: #555;
        }

        tbody tr {
            transition: all 0.2s ease;
        }

        tbody tr:hover {
            background: #f9f9f9;
        }

        /* ACTIONS */
        .btn-sm {
            padding: 4px 10px;
            font-size: 12px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            background: #f0f0f0;
            color: #666;
            transition: all 0.2s ease;
        }

        .btn-sm:hover {
            background: #667eea;
            color: white;
        }

        .btn-sm.delete {
            background: #ffebee;
            color: #c62828;
        }

        .btn-sm.delete:hover {
            background: #c62828;
            color: white;
        }

        /* ALERTS */
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 14px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .alert.success {
            background: #c8e6c9;
            color: #2e7d32;
            border-left: 4px solid #2e7d32;
        }

        .alert.error {
            background: #ffcdd2;
            color: #c62828;
            border-left: 4px solid #c62828;
        }

        /* SCROLLBAR */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f0f0f0;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }

        /* EDITOR TOOLBAR */
        .editor-toolbar {
            display: flex;
            gap: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }

        .editor-tool {
            padding: 6px 12px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
            color: #555;
        }

        .editor-tool:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .notes-editor {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            background: white;
            min-height: 150px;
            font-family: 'Segoe UI', monospace;
            font-size: 14px;
            line-height: 1.6;
            resize: vertical;
            transition: all 0.3s ease;
        }

        .notes-editor:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        @media (max-width: 1200px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>📚</h1>
            <div class="header-buttons">
                <button class="btn btn-primary" onclick="refreshData()">🔄 Yenile</button>
            </div>
        </div>

        <!-- MAIN CONTENT -->
        <div class="content">
            <!-- LEFT: FORM -->
            <div class="panel">
                <div class="tabs">
                    <button class="tab active" onclick="switchTab(event, 'words-tab')">📖 Kelimeler</button>
                    <button class="tab" onclick="switchTab(event, 'notes-tab')">📝 Notlar</button>
                </div>

                <!-- WORDS TAB -->
                <div id="words-tab" class="tab-content active">
                    <div id="message-words"></div>
                    <div class="form-group">
                        <label>Kelime</label>
                        <input type="text" id="word-input" placeholder="İngilizce kelime girin..." />
                    </div>
                    <div class="form-group">
                        <label>Anlamı</label>
                        <input type="text" id="meaning-input" placeholder="Türkçe anlamı girin..." />
                    </div>
                    <div class="form-group">
                        <label>Örnek Cümle</label>
                        <textarea id="sentence-input" placeholder="Örnek cümle girin..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Kaynak</label>
                        <input type="text" id="source-input" placeholder="Kaynak belirtin (örn: BBC, YouTube, vb.)" />
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-primary" onclick="addWord()">➕ Kelime Ekle</button>
                        <button class="btn btn-secondary" onclick="clearWordForm()">🗑️ Temizle</button>
                    </div>
                </div>

                <!-- NOTES TAB -->
                <div id="notes-tab" class="tab-content">
                    <div id="message-notes"></div>
                    <div class="form-group">
                        <label>Not Başlığı</label>
                        <input type="text" id="note-title" placeholder="Not başlığını girin..." />
                    </div>
                    <div class="form-group">
                        <label>Not İçeriği</label>
                        <div class="editor-toolbar">
                            <button class="editor-tool" onclick="formatText('bold')" title="Kalın">
                                <b>B</b>
                            </button>
                            <button class="editor-tool" onclick="formatText('italic')" title="İtalik">
                                <i>I</i>
                            </button>
                            <button class="editor-tool" onclick="formatText('underline')" title="Altını çiz">
                                <u>U</u>
                            </button>
                            <button class="editor-tool" onclick="formatText('insertUnorderedList')" title="Liste">
                                • Liste
                            </button>
                            <button class="editor-tool" onclick="insertLink()" title="Link">
                                🔗 Link
                            </button>
                        </div>
                        <div class="notes-editor" id="note-content" contenteditable="true"></div>
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-primary" onclick="addNote()">➕ Not Ekle</button>
                        <button class="btn btn-secondary" onclick="clearNoteForm()">🗑️ Temizle</button>
                    </div>
                </div>
            </div>

            <!-- RIGHT: DATA GRID -->
            <div class="right-panel">
                <div class="data-grid">
                    <h3>📊 Kelimeler</h3>
                    <div class="table-wrapper">
                        <table id="words-table">
                            <thead>
                                <tr>
                                    <th style="width: 15%;">Kelime</th>
                                    <th style="width: 20%;">Anlamı</th>
                                    <th style="width: 35%;">Örnek</th>
                                    <th style="width: 15%;">Kaynak</th>
                                    <th style="width: 10%;">İşlem</th>
                                </tr>
                            </thead>
                            <tbody id="words-body">
                                <tr><td colspan="5" style="text-align: center;">Yükleniyor...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="data-grid">
                    <h3>📄 Notlar</h3>
                    <div class="table-wrapper">
                        <table id="notes-table">
                            <thead>
                                <tr>
                                    <th style="width: 25%;">Başlık</th>
                                    <th style="width: 65%;">Önizleme</th>
                                    <th style="width: 10%;">İşlem</th>
                                </tr>
                            </thead>
                            <tbody id="notes-body">
                                <tr><td colspan="3" style="text-align: center;">Yükleniyor...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';

        function switchTab(event, tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }

        function showMessage(type, message, containerId) {
            const container = document.getElementById(containerId);
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${type}`;
            alertDiv.textContent = message;
            container.innerHTML = '';
            container.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 4000);
        }

        async function addWord() {
            const word = document.getElementById('word-input').value.trim();
            const meaning = document.getElementById('meaning-input').value.trim();
            const sentence = document.getElementById('sentence-input').value.trim();
            const source = document.getElementById('source-input').value.trim();

            if (!word || !meaning) {
                showMessage('error', '❌ Kelime ve anlamını doldurunuz!', 'message-words');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/words`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word, meaning, sentence, source })
                });

                if (!response.ok) {
                    showMessage('error', `❌ Hata: ${response.status}`, 'message-words');
                    return;
                }

                const text = await response.text();
                if (!text) {
                    showMessage('error', '❌ Boş yanıt', 'message-words');
                    return;
                }

                const data = JSON.parse(text);
                if (data.success) {
                    showMessage('success', '✅ Kelime başarıyla eklendi!', 'message-words');
                    clearWordForm();
                    await loadWords();
                } else {
                    showMessage('error', `❌ ${data.error}`, 'message-words');
                }
            } catch (error) {
                showMessage('error', `❌ Hata: ${error.message}`, 'message-words');
                console.error('addWord Error:', error);
            }
        }

        async function deleteWord(id) {
            if (!confirm('Bu kelimeyi silmek istediğinize emin misiniz?')) return;

            try {
                const response = await fetch(`${API_BASE}/words/${id}`, { method: 'DELETE' });
                if (!response.ok) {
                    console.error('Response error:', response.status);
                    return;
                }
                
                const text = await response.text();
                if (!text) {
                    console.error('Empty response');
                    return;
                }
                
                const data = JSON.parse(text);
                if (data.success) {
                    showMessage('success', '✅ Kelime silindi!', 'message-words');
                    await loadWords();
                } else {
                    showMessage('error', `❌ ${data.error}`, 'message-words');
                }
            } catch (error) {
                showMessage('error', `❌ ${error.message}`, 'message-words');
            }
        }

        async function loadWords() {
            try {
                const response = await fetch(`${API_BASE}/words`);
                if (!response.ok) {
                    console.error('Response error:', response.status);
                    return;
                }
                
                const text = await response.text();
                if (!text) {
                    console.error('Empty response');
                    return;
                }
                
                const data = JSON.parse(text);

                const tbody = document.getElementById('words-body');
                if (data.success && data.words && data.words.length > 0) {
                    tbody.innerHTML = data.words.map(w => `
                        <tr>
                            <td><strong>${escapeHtml(w.word)}</strong></td>
                            <td>${escapeHtml(w.meaning)}</td>
                            <td style="color: #777; font-size: 12px;">${escapeHtml((w.sentence || '').substring(0, 50))}</td>
                            <td>${escapeHtml(w.source || '-')}</td>
                            <td>
                                <button class="btn-sm delete" onclick="deleteWord(${w.id})">Sil</button>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999;">Kelime yok</td></tr>';
                }
            } catch (error) {
                console.error('loadWords Error:', error);
            }
        }

        function clearWordForm() {
            document.getElementById('word-input').value = '';
            document.getElementById('meaning-input').value = '';
            document.getElementById('sentence-input').value = '';
            document.getElementById('source-input').value = '';
        }

        async function addNote() {
            const title = document.getElementById('note-title').value.trim();
            const content = document.getElementById('note-content').innerHTML.trim();

            if (!title || !content) {
                showMessage('error', '❌ Başlık ve içeriği doldurunuz!', 'message-notes');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });

                if (!response.ok) {
                    showMessage('error', `❌ Hata: ${response.status}`, 'message-notes');
                    return;
                }

                const text = await response.text();
                if (!text) {
                    showMessage('error', '❌ Boş yanıt', 'message-notes');
                    return;
                }

                const data = JSON.parse(text);
                if (data.success) {
                    showMessage('success', '✅ Not eklendi!', 'message-notes');
                    clearNoteForm();
                    await loadNotes();
                } else {
                    showMessage('error', `❌ ${data.error}`, 'message-notes');
                }
            } catch (error) {
                showMessage('error', `❌ ${error.message}`, 'message-notes');
                console.error('addNote Error:', error);
            }
        }

        async function deleteNote(id) {
            if (!confirm('Bu notu silmek istediğinize emin misiniz?')) return;

            try {
                const response = await fetch(`${API_BASE}/notes/${id}`, { method: 'DELETE' });
                if (!response.ok) {
                    console.error('Response error:', response.status);
                    return;
                }
                
                const text = await response.text();
                if (!text) {
                    console.error('Empty response');
                    return;
                }
                
                const data = JSON.parse(text);
                if (data.success) {
                    showMessage('success', '✅ Not silindi!', 'message-notes');
                    await loadNotes();
                } else {
                    showMessage('error', `❌ ${data.error}`, 'message-notes');
                }
            } catch (error) {
                showMessage('error', `❌ ${error.message}`, 'message-notes');
            }
        }

        async function loadNotes() {
            try {
                const response = await fetch(`${API_BASE}/notes`);
                if (!response.ok) {
                    console.error('Response error:', response.status);
                    return;
                }
                
                const text = await response.text();
                if (!text) {
                    console.error('Empty response');
                    return;
                }
                
                const data = JSON.parse(text);

                const tbody = document.getElementById('notes-body');
                if (data.success && data.notes && data.notes.length > 0) {
                    tbody.innerHTML = data.notes.map(n => {
                        const preview = n.note.replace(/<[^>]*>/g, '').substring(0, 80);
                        return `
                            <tr>
                                <td><strong>${escapeHtml(n.title)}</strong></td>
                                <td style="font-size: 12px;">${escapeHtml(preview)}...</td>
                                <td>
                                    <button class="btn-sm delete" onclick="deleteNote(${n.id})">Sil</button>
                                </td>
                            </tr>
                        `;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">Not yok</td></tr>';
                }
            } catch (error) {
                console.error('loadNotes Error:', error);
            }
        }

        function clearNoteForm() {
            document.getElementById('note-title').value = '';
            document.getElementById('note-content').innerHTML = '';
        }

        function formatText(command) {
            document.getElementById('note-content').focus();
            document.execCommand(command, false, null);
        }

        function insertLink() {
            const url = prompt('URL girin:');
            if (url) {
                document.getElementById('note-content').focus();
                document.execCommand('createLink', false, url);
            }
        }

        async function refreshData() {
            await loadWords();
            await loadNotes();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        window.addEventListener('DOMContentLoaded', () => {
            loadWords();
            loadNotes();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/words', methods=['GET', 'POST'])
def handle_words():
    try:
        supabase = get_supabase()

        if request.method == 'GET':
            success, result = supabase.select('words')
            if success:
                return jsonify({'success': True, 'words': result if isinstance(result, list) else []})
            return jsonify({'success': False, 'error': result}), 500

        data = request.json
        word = data.get('word', '').strip()
        meaning = data.get('meaning', '').strip()
        sentence = data.get('sentence', '').strip() or None
        source = data.get('source', '').strip() or None

        if not word or not meaning:
            return jsonify({'success': False, 'error': 'Kelime ve anlamı zorunludur'}), 400

        success, result = supabase.insert('words', {
            'word': word,
            'meaning': meaning,
            'sentence': sentence,
            'source': source,
            'created_at': datetime.utcnow().isoformat()
        })

        if success:
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': result}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    try:
        supabase = get_supabase()
        success, result = supabase.delete('words', word_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notes', methods=['GET', 'POST'])
def handle_notes():
    try:
        supabase = get_supabase()

        if request.method == 'GET':
            success, result = supabase.select('notes')
            if success:
                return jsonify({'success': True, 'notes': result if isinstance(result, list) else []})
            return jsonify({'success': False, 'error': result}), 500

        data = request.json
        title = data.get('title', '').strip()
        note = data.get('content', '').strip()

        print(f"📝 Not ekleniyor:")
        print(f"  Başlık: {title[:30]}...")
        print(f"  İçerik: {note[:30]}...")

        if not title or not note:
            return jsonify({'success': False, 'error': 'Başlık ve içerik zorunludur'}), 400

        success, result = supabase.insert('notes', {
            'title': title,
            'note': note,
            'created_at': datetime.utcnow().isoformat()
        })

        if success:
            print(f"✅ Not başarıyla eklendi!")
            return jsonify({'success': True, 'data': result})
        else:
            print(f"❌ Not ekleme hatası: {result}")
            return jsonify({'success': False, 'error': result}), 500

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        supabase = get_supabase()
        success, result = supabase.delete('notes', note_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# LAUNCHER
# ==============================================================================

def start_server():
    """Flask sunucusunu başlat"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def main():
    """Ana giriş noktası"""
    print(f'''
╔════════════════════════════════════════════════════════════════╗
║         📚 VOCABULARY MANAGER - Modern Edition 📚               ║
║                                                                ║
║  ✅ Supabase URL ve Key kod içerisinde                        ║
║  ✅ SSL doğrulaması kapalı                                    ║
║  ✅ Ayarlar menüsü yok                                        ║
║                                                                ║
║  🌐 Tarayıcı: http://localhost:5000                           ║
║  🔑 Supabase URL: {SUPABASE_URL}
║                                                                ║
║  ⛔ Çıkmak: CTRL+C                                            ║
╚════════════════════════════════════════════════════════════════╝
    ''')

    # Sunucuyu ayrı thread'de çalıştır
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Tarayıcıyı aç
    import time
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000', new=2)
    except:
        print('⚠️  Tarayıcı otomatik açılamadı. http://localhost:5000 adresine gidin.')

    # Ana thread'ı çalışır durumda tut
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n\n✅ Uygulama kapatıldı.')
        sys.exit(0)


if __name__ == '__main__':
    main()