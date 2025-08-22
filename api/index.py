from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import requests
import base64
from openai import OpenAI

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # Обрабатываем GET запросы
        if self.path == '/' or self.path == '/index.html':
            self.serve_login_page()
        elif self.path == '/app':
            self.serve_main_page()
        else:
            self.send_error(404)
    
    def do_POST(self):
        # Обрабатываем POST запросы
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/login':
            self.handle_login()
        elif parsed_path.path == '/api/generate':
            self.handle_generate()
        else:
            self.send_error(404)
    
    def respond_json(self, data, status_code=200):
        """Отправляет JSON ответ с правильными заголовками"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def respond_html(self, html):
        """Отправляет HTML ответ"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_login_page(self):
        html = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🔐 Вход - AI Image Generator</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Montserrat', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}
.login-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    max-width: 400px;
    width: 100%;
    text-align: center;
}
.login-container h1 {
    color: #2c3e50;
    font-weight: 700;
    margin-bottom: 10px;
}
.login-container p {
    color: #666;
    margin-bottom: 30px;
}
input {
    font-family: inherit;
    font-size: 16px;
    padding: 15px;
    border: 2px solid #e1e8ed;
    border-radius: 12px;
    background: white;
    transition: all 0.3s ease;
    width: 100%;
    margin-bottom: 20px;
}
input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
.login-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 25px;
    font-family: inherit;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    width: 100%;
}
.login-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}
.error {
    color: #ff6b6b;
    margin-top: 15px;
    font-weight: 500;
}
</style>
</head>
<body>
    <div class="login-container">
        <h1>Ksenia's image generator</h1>
        <p>Введите секретный ключ для доступа</p>
        
        <form id="loginForm">
            <input type="password" id="secretKey" placeholder="Секретный ключ" required />
            <button type="submit" class="login-btn">Войти</button>
        </form>
        
        <div id="error"></div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('error');
            const secretKey = document.getElementById('secretKey').value;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret_key: secretKey })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    window.location.href = '/app';
                } else {
                    errorDiv.textContent = 'Неверный секретный ключ';
                    errorDiv.className = 'error';
                }
            } catch (error) {
                errorDiv.textContent = 'Ошибка подключения: ' + error.message;
                errorDiv.className = 'error';
            }
        });
    </script>
</body>
</html>'''
        
        self.respond_html(html)
    
    def handle_login(self):
        try:
            # Читаем данные запроса
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            secret_key = data.get('secret_key')
            expected_secret = os.environ.get('SECRET_KEY', '')
            
            if secret_key == expected_secret and expected_secret:
                self.respond_json({'success': True})
            else:
                self.respond_json({'success': False})
            
        except Exception as e:
            self.respond_json({'success': False, 'error': str(e)}, 500)
    
    def serve_main_page(self):
        # Проверяем наличие OpenAI API ключа
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        api_status = 'ok' if openai_key else 'missing'
        
        html = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎨 Ksenia's image generator</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Montserrat', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    color: #333;
}
.container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    max-width: 900px;
    width: 100%;
}
.header {
    text-align: center;
    margin-bottom: 30px;
}
.header h1 {
    color: #2c3e50;
    font-weight: 700;
    margin-bottom: 10px;
}
.api-status {
    padding: 15px 20px;
    border-radius: 12px;
    margin-bottom: 30px;
    font-weight: 500;
    text-align: center;
}
.api-ok {
    background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
    color: white;
}
.api-error {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
}
.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
    margin-bottom: 30px;
}
.form-group {
    display: flex;
    flex-direction: column;
}
label {
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 8px;
}
input, select, textarea {
    font-family: inherit;
    font-size: 16px;
    padding: 15px;
    border: 2px solid #e1e8ed;
    border-radius: 12px;
    background: white;
    transition: all 0.3s ease;
}
input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
textarea {
    resize: vertical;
    min-height: 120px;
}
.model-info {
    background: linear-gradient(135deg, #f8f9ff 0%, #e8edff 100%);
    padding: 12px 16px;
    border-radius: 10px;
    margin-top: 8px;
    font-size: 0.85rem;
    color: #5a67d8;
    border-left: 4px solid #667eea;
}
.cost-hint {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    font-size: 0.9rem;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
}
.cost-hint strong {
    color: #1e3a8a;
}
.cost-hint a {
    color: #2563eb;
    text-decoration: none;
}
.cost-hint a:hover {
    text-decoration: underline;
}
.generate-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 18px 40px;
    border-radius: 50px;
    font-family: inherit;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    width: 100%;
    margin-top: 20px;
}
.generate-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}
.status {
    margin: 25px 0;
    padding: 15px 20px;
    border-radius: 12px;
    font-weight: 500;
    text-align: center;
}
.status.success {
    background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
    color: white;
}
.status.error {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
}
.images-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 25px;
    margin-top: 30px;
}
.image-card {
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    position: relative;
}
.image-card:hover {
    transform: translateY(-5px);
}
.image-card img {
    width: 100%;
    height: auto;
    display: block;
}
.image-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
    opacity: 0;
    transition: opacity 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}
.image-card:hover .image-overlay {
    opacity: 1;
}
.download-btn {
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    color: white;
    text-decoration: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    border: 2px solid rgba(255,255,255,0.3);
}
.balance-link {
    text-align: center;
    margin: 15px 0;
    font-size: 14px;
}
.balance-link a {
    color: #667eea;
    text-decoration: none;
}
@media (max-width: 768px) {
    .container {
        padding: 25px;
        margin: 10px;
    }
    .form-grid {
        grid-template-columns: 1fr;
        gap: 20px;
    }
}
</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ksenia's lustfull image generator</h1>
        </div>
        
        <div id="apiStatus" class="api-status ''' + ('api-ok' if api_status == 'ok' else 'api-error') + '''">
            ''' + ('✅ OpenAI API подключен и готов к работе' if api_status == 'ok' else '❌ OpenAI API ключ не найден в окружении') + '''
        </div>
        
        <form id="imageForm">
            <div class="form-grid">
                <div class="form-group">
                    <label for="model">Модель:</label>
                    <select id="model" name="model" onchange="updateModelOptions(); updateCostHint();">
                        <option value="gpt-image-1">GPT Image 1 (Лучшее качество)</option>
                        <option value="dall-e-3">DALL-E 3 (Высокое качество)</option>
                        <option value="dall-e-2">DALL-E 2 (Быстро и доступно)</option>
                    </select>
                    <div id="modelInfo" class="model-info"></div>
                </div>
                
                <div class="form-group">
                    <label for="size">Размер изображения:</label>
                    <select id="size" name="size" onchange="updateCostHint();"></select>
                </div>
                
                <div class="form-group" id="qualityGroup">
                    <label for="quality">Качество:</label>
                    <select id="quality" name="quality" onchange="updateCostHint();"></select>
                </div>
                
                <div class="form-group" id="styleGroup">
                    <label for="style">Стиль (DALL-E 3):</label>
                    <select id="style" name="style">
                        <option value="vivid">Яркий</option>
                        <option value="natural">Естественный</option>
                    </select>
                </div>
                
                <div class="form-group" id="backgroundGroup">
                    <label for="background">Фон (GPT Image 1):</label>
                    <select id="background" name="background">
                        <option value="auto">Авто (по умолчанию)</option>
                        <option value="transparent">Прозрачный</option>
                        <option value="opaque">Непрозрачный</option>
                    </select>
                </div>
                
                <div class="form-group" id="moderationGroup">
                    <label for="moderation">Модерация (GPT Image 1):</label>
                    <select id="moderation" name="moderation">
                        <option value="low">Низкая (менее строгая)</option>
                        <option value="auto">Авто (стандартная)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="n">Количество изображений:</label>
                    <select id="n" name="n" onchange="updateCostHint();">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label for="prompt">Описание изображения:</label>
                <textarea id="prompt" name="prompt" placeholder="Опишите изображение, которое хотите создать..." required></textarea>
            </div>
            
            <!-- Информация о стоимости -->
            <div id="costHint" class="cost-hint">
                Загружается информация о стоимости...
            </div>
            
            <button type="submit" class="generate-btn">
                Создать изображения
            </button>
        </form>
        
        <div class="balance-link">
            💰 <a href="https://platform.openai.com/settings/organization/billing/overview" target="_blank">Проверить баланс в OpenAI</a>
        </div>
        
        <div id="status"></div>
        <div id="images" class="images-grid"></div>
    </div>

    <script>
        // Данные о ценах (актуальные по состоянию на 2025)
        const priceData = {
            "gpt-image-1": {
                "1024x1024": { "low": 0.011, "medium": 0.042, "high": 0.167, "auto": 0.042 },
                "1024x1536": { "low": 0.016, "medium": 0.063, "high": 0.250, "auto": 0.063 },
                "1536x1024": { "low": 0.016, "medium": 0.063, "high": 0.250, "auto": 0.063 }
            },
            "dall-e-3": {
                "1024x1024": { "standard": 0.040, "hd": 0.080 },
                "1024x1792": { "standard": 0.080, "hd": 0.120 },
                "1792x1024": { "standard": 0.080, "hd": 0.120 }
            },
            "dall-e-2": {
                "1024x1024": { "standard": 0.020 },
                "512x512": { "standard": 0.018 },
                "256x256": { "standard": 0.016 }
            }
        };

        function updateCostHint() {
            const model = document.getElementById('model').value;
            const size = document.getElementById('size').value;
            const quality = document.getElementById('quality').value;
            const n = parseInt(document.getElementById('n').value);
            
            if (!model || !size || !quality) return;
            
            const costPerImage = priceData[model]?.[size]?.[quality] || 0;
            const totalCost = costPerImage * n;
            
            const costHint = document.getElementById('costHint');
            costHint.innerHTML = `
                <strong>💰 Стоимость генерации:</strong><br>
                За 1 изображение: <strong>$${costPerImage.toFixed(4)}</strong><br>
                Общая стоимость (${n} изобр.): <strong>$${totalCost.toFixed(4)}</strong><br>
                <a href="https://platform.openai.com/docs/pricing#image-generation" target="_blank">📊 Подробнее о ценах</a>
            `;
        }

        function updateModelOptions() {
            const model = document.getElementById('model').value;
            const sizeSelect = document.getElementById('size');
            const qualityGroup = document.getElementById('qualityGroup');
            const qualitySelect = document.getElementById('quality');
            const styleGroup = document.getElementById('styleGroup');
            const backgroundGroup = document.getElementById('backgroundGroup');
            const moderationGroup = document.getElementById('moderationGroup');
            const infoDiv = document.getElementById('modelInfo');
            
            sizeSelect.innerHTML = '';
            qualitySelect.innerHTML = '';
            
            if (model === 'gpt-image-1') {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024 (Квадрат)</option>
                    <option value="1024x1536">1024×1536 (Портрет)</option>
                    <option value="1536x1024">1536×1024 (Пейзаж)</option>
                `;
                qualitySelect.innerHTML = `
                    <option value="auto" selected>Авто (по умолчанию)</option>
                    <option value="low">Низкое</option>
                    <option value="medium">Среднее</option>
                    <option value="high">Высокое</option>
                `;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'block';
                moderationGroup.style.display = 'block';
                infoDiv.innerHTML = '🚀 Новейшая модель с лучшим качеством, пониманием текста и поддержкой прозрачного фона. Может занимать до 2 минут.';
            } else if (model === 'dall-e-3') {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024 (Квадрат)</option>
                    <option value="1024x1792">1024×1792 (Портрет)</option>
                    <option value="1792x1024">1792×1024 (Пейзаж)</option>
                `;
                qualitySelect.innerHTML = `
                    <option value="standard" selected>Стандартное</option>
                    <option value="hd">HD</option>
                `;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'block';
                backgroundGroup.style.display = 'none';
                moderationGroup.style.display = 'none';
                infoDiv.innerHTML = '🎨 Высокое качество изображений и понимание сложных описаний.';
            } else {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024</option>
                    <option value="512x512">512×512</option>
                    <option value="256x256">256×256</option>
                `;
                qualitySelect.innerHTML = `<option value="standard">Стандартное</option>`;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'none';
                moderationGroup.style.display = 'none';
                infoDiv.innerHTML = '⚡ Быстрая генерация изображений по доступной цене.';
            }
        }
        
        updateModelOptions();
        updateCostHint();
        
        document.getElementById('imageForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const imagesDiv = document.getElementById('images');
            const model = document.getElementById('model').value;
            
            if (model === 'gpt-image-1') {
                statusDiv.innerHTML = '<div class="status">⏳ GPT Image 1 может занимать до 2 минут...</div>';
            } else {
                statusDiv.innerHTML = '<div class="status">Генерируем изображения...</div>';
            }
            
            imagesDiv.innerHTML = '';
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = '<div class="status success">✨ Изображения успешно созданы!</div>';
                    
                    result.images.forEach((imageData, index) => {
                        const card = document.createElement('div');
                        card.className = 'image-card';
                        
                        card.innerHTML = `
                            <img src="data:image/png;base64,${imageData}" alt="Generated Image ${index + 1}">
                            <div class="image-overlay">
                                <a href="data:image/png;base64,${imageData}" download="ai_image_${index + 1}.png" class="download-btn">
                                    📥 Скачать
                                </a>
                            </div>
                        `;
                        
                        imagesDiv.appendChild(card);
                    });
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ ${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ Ошибка сети: ${error.message}</div>`;
            }
        });
    </script>
</body>
</html>'''
        
        self.respond_html(html)
    
    def handle_generate(self):
        try:
            # Получаем API ключ из окружения
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                self.respond_json({'success': False, 'error': 'OpenAI API ключ не настроен на сервере'}, 500)
                return
            
            # Инициализируем OpenAI клиент
            client = OpenAI(api_key=api_key)
            
            # Читаем данные запроса
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Получаем параметры
            model = data.get('model')
            size = data.get('size')
            quality = data.get('quality')
            style = data.get('style')
            background = data.get('background')
            moderation = data.get('moderation')
            n = int(data.get('n', 1))
            prompt = data.get('prompt')
            
            if not prompt:
                self.respond_json({'success': False, 'error': 'Описание изображения обязательно'}, 400)
                return
            
            # Собираем параметры для OpenAI API
            params = {
                "model": model,
                "prompt": prompt,
                "n": n,
                "size": size
            }
            
            # Параметры для GPT Image 1 (согласно документации)
            if model == "gpt-image-1":
                # Quality: low, medium, high, auto
                if quality and quality in ["low", "medium", "high", "auto"]:
                    params["quality"] = quality
                # Background: transparent, opaque, auto
                if background and background in ["transparent", "opaque", "auto"]:
                    params["background"] = background
                # Moderation: auto (standard), low (less restrictive)
                if moderation and moderation in ["auto", "low"]:
                    params["moderation"] = moderation
                    
            elif model == "dall-e-3":
                if quality and quality in ["standard", "hd"]:
                    params["quality"] = quality
                else:
                    params["quality"] = "standard"
                if style and style in ["vivid", "natural"]:
                    params["style"] = style
                else:
                    params["style"] = "vivid"
            
            # Генерируем изображения
            openai_response = client.images.generate(**params)
            
            if not hasattr(openai_response, 'data') or not openai_response.data:
                self.respond_json({'success': False, 'error': 'Неверный ответ от OpenAI API'}, 500)
                return
            
            # Обрабатываем изображения
            images = []
            for i, image_data in enumerate(openai_response.data):
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    images.append(image_data.b64_json)
                elif hasattr(image_data, 'url') and image_data.url:
                    try:
                        image_response = requests.get(image_data.url, timeout=60)
                        if image_response.status_code == 200:
                            image_b64 = base64.b64encode(image_response.content).decode('utf-8')
                            images.append(image_b64)
                        else:
                            self.respond_json({'success': False, 'error': f'Ошибка загрузки изображения {i+1}'}, 500)
                            return
                    except requests.exceptions.RequestException as e:
                        self.respond_json({'success': False, 'error': f'Ошибка загрузки: {str(e)}'}, 500)
                        return
                else:
                    self.respond_json({'success': False, 'error': f'Изображение {i+1} не содержит данных'}, 500)
                    return
            
            # Возвращаем результат
            self.respond_json({'success': True, 'images': images})
            
        except Exception as e:
            self.respond_json({'success': False, 'error': str(e)}, 500)
