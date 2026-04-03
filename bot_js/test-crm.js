// test-crm.js - тест подключения к CRM
const axios = require('axios');

const CRM_URL = 'http://localhost:5001/api/messages';

async function testCRM() {
    console.log('🔍 Проверка CRM...');
    
    try {
        // Проверка health
        const health = await axios.get('http://localhost:5001/api/health');
        console.log('✅ CRM Health:', health.data);
        
        // Тестовое сообщение
        const testData = {
            source: 'test',
            chat_id: 'test123',
            user_id: 'test456',
            user_name: 'Test User',
            text: 'Тестовое сообщение',
            photos: ['https://picsum.photos/300/200'],
            received_at: new Date().toISOString()
        };
        
        const response = await axios.post(CRM_URL, testData);
        console.log('✅ Тестовое сообщение сохранено:', response.data);
        
        // Получение списка
        const messages = await axios.get('http://localhost:5001/api/messages');
        console.log(`✅ Всего сообщений в CRM: ${messages.data.length}`);
        
    } catch (error) {
        console.error('❌ Ошибка:', error.message);
        if (error.code === 'ECONNREFUSED') {
            console.error('❌ CRM не запущен! Запустите: python crm_backend.py');
        }
    }
}

testCRM();