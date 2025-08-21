from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Инициализация клиента OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>OpenAI Image Generator</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { height: 100px; resize: vertical; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .images { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
        .image-container { max-width: 300px; }
        .image-container img { width: 100%; height: auto; border-radius: 4px; }
        .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .warning { background-color: #fff3cd; color: #856404; }
        .api-status { padding: 10px; margin-bottom: 20px; border-radius: 4px; font-weight: bold; }
        .api-ok { background-color: #d1ecf1; color: #0c5460; }
        .api-error { background-color: #f8d7da; color: #721c24; }
        .model-info { background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>OpenAI Image Generator</h1>
    
    <div id="apiStatus" class="api-status"></div>
    
    <form id="imageForm">
        <div class="form-group">
            <label for="model">Model:</label>
            <select id="model" name="model" onchange="updateModelOptions()">
                <option value="gpt-image-1">GPT Image 1 (Latest, Best Quality)</option>
                <option value="dall-e-3">DALL-E 3 (High Quality)</option>
                <option value="dall-e-2">DALL-E 2 (Fast & Affordable)</option>
            </select>
            <div id="modelInfo" class="model-info"></div>
        </div>
        
        <div class="form-group">
            <label for="size">Image Size:</label>
            <select id="size" name="size">
                <!-- Опции будут обновляться в зависимости от модели -->
            </select>
        </div>
        
        <div class="form-group" id="qualityGroup">
            <label for="quality">Quality:</label>
            <select id="quality" name="quality">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="standard">Standard</option>
                <option value="hd">HD</option>
            </select>
        </div>
        
        <div class="form-group" id="styleGroup">
            <label for="style">Style (DALL-E 3 only):</label>
            <select id="style" name="style">
                <option value="vivid">Vivid</option>
                <option value="natural">Natural</option>
            </select>
        </div>
        
        <div class="form-group" id="backgroundGroup">
            <label for="background">Background (GPT Image 1):</label>
            <select id="background" name="background">
                <option value="">Default</option>
                <option value="transparent">Transparent</option>
                <option value="opaque">Opaque</option>
                <option value="auto">Auto</option>
            </select>
        </div>
        
        <div class="form-group" id="moderationGroup">
            <label for="moderation">Moderation (GPT Image 1):</label>
            <select id="moderation" name="moderation">
                <option value="low">Low (Less restrictive)</option>
                <option value="auto">Auto (Standard)</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="n">Number of Images:</label>
            <select id="n" name="n">
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="prompt">Prompt:</label>
            <textarea id="prompt" name="prompt" placeholder="Опишите изображение, которое хотите создать..." required></textarea>
        </div>
        
        <button type="submit">Generate Images</button>
    </form>
    
    <div id="status"></div>
    <div id="images" class="images"></div>
    
    <script>
        function updateModelOptions() {
            const model = document.getElementById('model').value;
            const sizeSelect = document.getElementById('size');
            const qualityGroup = document.getElementById('qualityGroup');
            const qualitySelect = document.getElementById('quality');
            const styleGroup = document.getElementById('styleGroup');
            const backgroundGroup = document.getElementById('backgroundGroup');
            const moderationGroup = document.getElementById('moderationGroup');
            const infoDiv = document.getElementById('modelInfo');
            
            // Очищаем размеры и качество
            sizeSelect.innerHTML = '';
            qualitySelect.innerHTML = '';
            
            if (model === 'gpt-image-1') {
                // GPT Image 1 размеры и параметры
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024x1024 (Square)</option>
                    <option value="1024x1536">1024x1536 (Portrait)</option>
                    <option value="1536x1024">1536x1024 (Landscape)</option>
                `;
                qualitySelect.innerHTML = `
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                `;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'block';
                moderationGroup.style.display = 'block';
                infoDiv.innerHTML = '🚀 GPT Image 1: Новейшая модель, лучшее качество, понимание текста, может занимать до 2 минут';
            } else if (model === 'dall-e-3') {
                // DALL-E 3 размеры и параметры
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024x1024 (Square)</option>
                    <option value="1024x1792">1024x1792 (Portrait)</option>
                    <option value="1792x1024">1792x1024 (Landscape)</option>
                `;
                qualitySelect.innerHTML = `
                    <option value="standard" selected>Standard</option>
                    <option value="hd">HD</option>
                `;
                qualityGroup.style.display = 'block';
                styleGroup.style.display = 'block';
                backgroundGroup.style.display = 'none';
                moderationGroup.style.display = 'none';
                infoDiv.innerHTML = '🎨 DALL-E 3: Высокое качество, понимание сложных промптов, поддержка HD';
            } else {
                // DALL-E 2 размеры и параметры
                sizeSelect.innerHTML = `
                    <option value="1024x1024">1024x1024</option>
                    <option value="512x512">512x512</option>
                    <option value="256x256">256x256</option>
                `;
                qualityGroup.style.display = 'none';
                styleGroup.style.display = 'none';
                backgroundGroup.style.display = 'none';
                moderationGroup.style.display = 'none';
                infoDiv.innerHTML = '⚡ DALL-E 2: Быстрая генерация, базовые возможности, доступная цена';
            }
        }
        
        // Инициализация
        updateModelOptions();
        
        // Проверяем статус API ключа
        fetch('/api-status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('apiStatus');
                if (data.hasKey) {
                    statusDiv.innerHTML = '✅ OpenAI API ключ загружен из .env файла';
                    statusDiv.className = 'api-status api-ok';
                } else {
                    statusDiv.innerHTML = '❌ OpenAI API ключ не найден в .env файле (OPENAI_API_KEY)';
                    statusDiv.className = 'api-status api-error';
                }
            });
    
        document.getElementById('imageForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const imagesDiv = document.getElementById('images');
            const model = document.getElementById('model').value;
            
            // Показываем предупреждение о времени генерации для GPT Image 1
            if (model === 'gpt-image-1') {
                statusDiv.innerHTML = '<div class="status warning">⏳ GPT Image 1 может занимать до 2 минут для сложных промптов...</div>';
            } else {
                statusDiv.innerHTML = '<div class="status">Generating images...</div>';
            }
            
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
                    statusDiv.innerHTML = '<div class="status success">Images generated successfully!</div>';
                    
                    result.images.forEach((imageData, index) => {
                        const container = document.createElement('div');
                        container.className = 'image-container';
                        
                        const img = document.createElement('img');
                        img.src = 'data:image/png;base64,' + imageData;
                        img.alt = 'Generated Image ' + (index + 1);
                        
                        const downloadLink = document.createElement('a');
                        downloadLink.href = 'data:image/png;base64,' + imageData;
                        downloadLink.download = 'generated_image_' + (index + 1) + '.png';
                        downloadLink.textContent = 'Download';
                        downloadLink.style.display = 'block';
                        downloadLink.style.marginTop = '5px';
                        
                        container.appendChild(img);
                        container.appendChild(downloadLink);
                        imagesDiv.appendChild(container);
                    });
                } else {
                    statusDiv.innerHTML = '<div class="status error">Error: ' + result.error + '</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = '<div class="status error">Network error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api-status')
def api_status():
    return jsonify({'hasKey': bool(client.api_key)})

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        
        if not client.api_key:
            return jsonify({
                'success': False, 
                'error': 'OpenAI API key not found. Please add OPENAI_API_KEY to your .env file'
            })
        
        model = data.get('model')
        size = data.get('size')
        quality = data.get('quality')
        style = data.get('style')
        background = data.get('background')
        moderation = data.get('moderation')
        n = int(data.get('n', 1))
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'})
        
        # Базовые параметры для всех моделей
        params = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        # Добавляем специфичные параметры для каждой модели
        if model == "gpt-image-1":
            # GPT Image 1 параметры
            if quality and quality in ["low", "medium", "high"]:
                params["quality"] = quality
            if background and background in ["transparent", "opaque", "auto"]:
                params["background"] = background
            if moderation and moderation in ["low", "auto"]:
                params["moderation"] = moderation
                
        elif model == "dall-e-3":
            # DALL-E 3 параметры
            if quality and quality in ["standard", "hd"]:
                params["quality"] = quality
            else:
                params["quality"] = "standard"
            if style and style in ["vivid", "natural"]:
                params["style"] = style
            else:
                params["style"] = "vivid"
        
        # DALL-E 2 не требует дополнительных параметров
        
        print(f"Generating with model: {model}")
        print(f"Parameters: {params}")
        
        # Генерируем изображения через Image API
        response = client.images.generate(**params)
        
        print(f"API Response received: {len(response.data) if response.data else 0} images")
        
        # Проверяем ответ
        if not hasattr(response, 'data') or not response.data:
            return jsonify({'success': False, 'error': 'Invalid response from OpenAI API'})
        
        # Конвертируем в base64
        images = []
        for i, image_data in enumerate(response.data):
            # GPT Image 1 возвращает b64_json напрямую
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                print(f"Using b64_json for image {i+1}")
                images.append(image_data.b64_json)
            # DALL-E модели возвращают URL
            elif hasattr(image_data, 'url') and image_data.url:
                print(f"Downloading from URL for image {i+1}: {image_data.url}")
                try:
                    image_response = requests.get(image_data.url, timeout=60)
                    if image_response.status_code == 200:
                        image_b64 = base64.b64encode(image_response.content).decode('utf-8')
                        images.append(image_b64)
                    else:
                        return jsonify({'success': False, 'error': f'Failed to download image {i+1}: HTTP {image_response.status_code}'})
                except requests.exceptions.RequestException as e:
                    return jsonify({'success': False, 'error': f'Failed to download image {i+1}: {str(e)}'})
            else:
                return jsonify({'success': False, 'error': f'Image {i+1} has no valid data'})
        
        return jsonify({'success': True, 'images': images})
        
    except Exception as e:
        print(f"Generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    if not client.api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file with: OPENAI_API_KEY=your_api_key_here")
    else:
        print("✅ OpenAI API key loaded from .env")
    
    print("Starting OpenAI Image Generator...")
    print("🎨 Available models:")
    print("  🚀 GPT Image 1 - Latest, best quality, supports transparency")
    print("  ⭐ DALL-E 3 - High quality with style options")  
    print("  ⚡ DALL-E 2 - Fast and affordable")
    print("Open http://localhost:5001 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5001)
