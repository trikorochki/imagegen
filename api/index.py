from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎨 AI Image Generator</title>
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
            <h1>🎨 AI Image Generator</h1>
            <p style="color: #666;">Создавайте удивительные изображения с помощью ИИ</p>
        </div>
        
        <form id="imageForm">
            <div class="form-group">
                <label for="api_key">OpenAI API Key:</label>
                <input type="password" id="api_key" name="api_key" placeholder="sk-..." required />
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="model">Модель:</label>
                    <select id="model" name="model" onchange="updateModelOptions()">
                        <option value="gpt-image-1">GPT Image 1 (Лучшее качество)</option>
                        <option value="dall-e-3">DALL-E 3 (Высокое качество)</option>
                        <option value="dall-e-2">DALL-E 2 (Быстро и доступно)</option>
                    </select>
                    <div id="modelInfo" class="model-info"></div>
                </div>
                
                <div class="form-group">
                    <label for="size">Размер изображения:</label>
                    <select id="size" name="size"></select>
                </div>
                
                <div class="form-group" id="qualityGroup">
                    <label for="quality">Качество:</label>
                    <select id="quality" name="quality"></select>
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
                        <option value="">По умолчанию</option>
                        <option value="transparent">Прозрачный</option>
                        <option value="white">Белый</option>
                        <option value="black">Черный</option>
                    </select>
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
        function updateModelOptions() {
            const model = document.getElementById('model').value;
            const sizeSelect = document.getElementById('size');
            const qualityGroup = document.getElementById('qualityGroup');
            const qualitySelect = document.getElementById('quality');
            const styleGroup = document.getElementById('styleGroup');
            const backgroundGroup = document.getElementById('backgroundGroup');
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
                    <option value="low">Низкое</option>
                    <option value="medium" selected>Среднее</option>
                    <option value="high">Высокое</option>
                `;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'block';
                infoDiv.innerHTML = '🚀 Новейшая модель с лучшим качеством и пониманием текста. Может занимать до 2 минут.';
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
                infoDiv.innerHTML = '🎨 Высокое качество изображений и понимание сложных описаний.';
            } else {
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024×1024</option>
                    <option value="512x512">512×512</option>
                    <option value="256x256">256×256</option>
                `;
                qualityGroup.style.display = 'none';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'none';
                infoDiv.innerHTML = '⚡ Быстрая генерация изображений по доступной цене.';
            }
        }
        
        updateModelOptions();
        
        document.getElementById('imageForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const imagesDiv = document.getElementById('images');
            const model = document.getElementById('model').value;
            
            if (model === 'gpt-image-1') {
                statusDiv.innerHTML = '<div class="status">⏳ GPT Image 1 может занимать до 2 минут для качественного результата...</div>';
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
        
        self.wfile.write(html.encode('utf-8'))
