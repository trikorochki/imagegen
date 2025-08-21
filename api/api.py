from flask import Flask, request, jsonify, session, render_template_string
from flask_session import Session
from functools import wraps
import os
from openai import OpenAI  
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
Session(app)

def get_openai_client():
    api_key = session.get('api_key')
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'api_key' not in session:
            return jsonify({'error': 'API key required'}), 401
        return f(*args, **kwargs)
    return decorated_function

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <title>🎨 AI Image Generator</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
            max-width: 500px;
            width: 100%;
            text-align: center;
        }
        
        .login-container h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .api-key-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e8ed;
            border-radius: 12px;
            font-family: inherit;
            font-size: 16px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        .api-key-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .submit-btn {
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
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        }
        
        .balance-link {
            margin-top: 15px;
            font-size: 14px;
            color: #5a67d8;
        }
        
        .balance-link a {
            color: #667eea;
            text-decoration: none;
        }
        
        .balance-link a:hover {
            text-decoration: underline;
        }
        
        .main-app {
            display: none;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            max-width: 900px;
            width: 100%;
            color: #333;
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
        
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
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
        
        @media (max-width: 768px) {
            .main-app {
                padding: 25px;
                margin: 10px;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="login-container" id="login-container">
        <h2>🎨 AI Image Generator</h2>
        <p style="color: #666; margin-bottom: 25px;">Введите ваш OpenAI API ключ для начала работы</p>
        <input type="password" id="api-key-input" class="api-key-input" placeholder="sk-..." />
        <br />
        <button id="submit-key" class="submit-btn">Войти</button>
        <div class="balance-link">
            💰 <a href="https://platform.openai.com/settings/organization/billing/overview" target="_blank">Проверить баланс в OpenAI</a>
        </div>
    </div>

    <div id="main-app" class="main-app">
        <button id="logout" class="logout-btn">Выйти</button>
        
        <div class="header">
            <h1>🎨 AI Image Generator</h1>
            <p style="color: #666;">Создавайте удивительные изображения с помощью ИИ</p>
        </div>
        
        <form id="imageForm">
            <div class="form-grid">
                <div class="form-group">
                    <label for="model">Модель:</label>
                    <select id="model" name="model" onchange="updateModelOptions()">
                        <option value="gpt-image-1">GPT Image 1 (Лучшее качество)</option>
                        <option value="dall-e-3">DALL-E 3 (Высокое качество)</option>
                        <option value="dall-e-2">DALL-E 2 (Быстро и доступно)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="size">Размер изображения:</label>
                    <select id="size" name="size"></select>
                </div>
                
                <div class="form-group" id="qualityGroup">
                    <label for="quality">Качество:</label>
                    <select id="quality" name="quality"></select>
                </div>
                
                <div class="form-group">
                    <label for="n">Количество изображений:</label>
                    <select id="n" name="n">
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
            
            <button type="submit" class="generate-btn" id="generateBtn">
                Создать изображения
            </button>
        </form>
        
        <div id="status"></div>
        <div id="images" class="images-grid"></div>
    </div>

    <script>
        const loginContainer = document.getElementById('login-container');
        const mainApp = document.getElementById('main-app');
        const submitKeyBtn = document.getElementById('submit-key');
        const apiKeyInput = document.getElementById('api-key-input');
        const logoutBtn = document.getElementById('logout');
        
        // Проверяем, есть ли уже API ключ в сессии
        async function checkApiKey() {
            try {
                const res = await fetch('/check-key');
                const data = await res.json();
                if (data.has_key) {
                    showMainApp();
                }
            } catch (e) {
                console.log('Session check failed');
            }
        }
        
        function showMainApp() {
            loginContainer.style.display = 'none';
            mainApp.style.display = 'block';
            updateModelOptions();
        }
        
        function showLogin() {
            mainApp.style.display = 'none';
            loginContainer.style.display = 'block';
            apiKeyInput.value = '';
        }
        
        submitKeyBtn.onclick = async () => {
            const key = apiKeyInput.value.trim();
            if (!key.startsWith('sk-')) {
                alert('Пожалуйста, введите корректный OpenAI API ключ (начинается с sk-)');
                return;
            }
            
            try {
                const res = await fetch('/set-key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({api_key: key})
                });
                const data = await res.json();
                if (data.success) {
                    showMainApp();
                } else {
                    alert('Не удалось сохранить API ключ');
                }
            } catch (e) {
                alert('Ошибка: ' + e.message);
            }
        };
        
        logoutBtn.onclick = async () => {
            await fetch('/logout', {method: 'POST'});
            showLogin();
        };
        
        function updateModelOptions() {
            const model = document.getElementById('model').value;
            const sizeSelect = document.getElementById('size');
            const qualitySelect = document.getElementById('quality');
            
            sizeSelect.innerHTML = '';
            qualitySelect.innerHTML = '';
            
            if (model === 'gpt-image-1') {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024 (Квадрат)</option>
                    <option value="1024x1536">1024×1536 (Портрет)</option>
                    <option value="1536x1024">1536×1024 (Пейзаж)</option>
                `;
                qualitySelect.innerHTML = `
                    <option value="low">Низкое</option>
                    <option value="medium" selected>Среднее</option>
                    <option value="high">Высокое</option>
                `;
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
            } else {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024</option>
                    <option value="512x512">512×512</option>
                    <option value="256x256">256×256</option>
                `;
                qualitySelect.innerHTML = `<option value="standard">Стандартное</option>`;
            }
        }
        
        document.getElementById('imageForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const imagesDiv = document.getElementById('images');
            const generateBtn = document.getElementById('generateBtn');
            
            generateBtn.disabled = true;
            generateBtn.textContent = 'Создаем изображения...';
            statusDiv.innerHTML = '<div class="status">Генерируем изображения...</div>';
            imagesDiv.innerHTML = '';
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/generate', {
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
                statusDiv.innerHTML = `<div class="status error">❌ Ошибка: ${error.message}</div>`;
            }
            
            generateBtn.disabled = false;
            generateBtn.textContent = 'Создать изображения';
        });
        
        // Проверяем API ключ при загрузке страницы
        checkApiKey();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/set-key', methods=['POST'])
def set_key():
    data = request.get_json()
    key = data.get('api_key')
    if not key or not key.startswith('sk-'):
        return jsonify({'success': False})
    session['api_key'] = key
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('api_key', None)
    return jsonify({'success': True})

@app.route('/check-key')
def check_key():
    return jsonify({'has_key': 'api_key' in session})

@app.route('/generate', methods=['POST'])
@require_api_key
def generate_image():
    try:
        data = request.get_json()
        client = get_openai_client()
        
        if not client:
            return jsonify({'success': False, 'error': 'API ключ отсутствует'})
        
        model = data.get('model')
        size = data.get('size')
        quality = data.get('quality')
        n = int(data.get('n', 1))
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Описание изображения обязательно'})
        
        params = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        if model == "gpt-image-1":
            if quality and quality in ["low", "medium", "high"]:
                params["quality"] = quality
        elif model == "dall-e-3":
            if quality and quality in ["standard", "hd"]:
                params["quality"] = quality
            else:
                params["quality"] = "standard"
            params["style"] = "vivid"
        
        response = client.images.generate(**params)
        
        if not hasattr(response, 'data') or not response.data:
            return jsonify({'success': False, 'error': 'Неверный ответ от OpenAI API'})
        
        images = []
        for i, image_data in enumerate(response.data):
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                images.append(image_data.b64_json)
            elif hasattr(image_data, 'url') and image_data.url:
                try:
                    image_response = requests.get(image_data.url, timeout=60)
                    if image_response.status_code == 200:
                        image_b64 = base64.b64encode(image_response.content).decode('utf-8')
                        images.append(image_b64)
                    else:
                        return jsonify({'success': False, 'error': f'Ошибка загрузки изображения {i+1}'})
                except requests.exceptions.RequestException as e:
                    return jsonify({'success': False, 'error': f'Ошибка загрузки: {str(e)}'})
            else:
                return jsonify({'success': False, 'error': f'Изображение {i+1} не содержит данных'})
        
        return jsonify({'success': True, 'images': images})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
