import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Home Component
const Home = () => {
  const [botStatus, setBotStatus] = useState(null);

  const checkBotStatus = async () => {
    try {
      const response = await axios.get(`${API}/`);
      setBotStatus(response.data);
      console.log('Bot Status:', response.data);
    } catch (e) {
      console.error(e, `Error checking bot status`);
    }
  };

  useEffect(() => {
    checkBotStatus();
    // Check status every 10 seconds
    const interval = setInterval(checkBotStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            🤖 Discord Server Creator
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            أنشئ سيرفرات Discord من ملفات JSON بسهولة
          </p>
          
          {/* Bot Status */}
          <div className="bg-gray-800 p-4 rounded-lg mb-8 max-w-md mx-auto">
            <h3 className="text-lg font-semibold text-white mb-2">حالة البوت</h3>
            {botStatus ? (
              <div>
                <div className={`flex items-center justify-center space-x-2 ${botStatus.bot_ready ? 'text-green-400' : 'text-red-400'}`}>
                  <div className={`w-3 h-3 rounded-full ${botStatus.bot_ready ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span>{botStatus.bot_ready ? 'متصل' : 'غير متصل'}</span>
                </div>
                {botStatus.bot_user && (
                  <p className="text-gray-400 text-sm mt-2">البوت: {botStatus.bot_user}</p>
                )}
              </div>
            ) : (
              <div className="text-gray-400">جاري التحميل...</div>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <Link to="/upload" className="group">
            <div className="bg-gray-800 p-8 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105">
              <div className="text-4xl mb-4">📤</div>
              <h3 className="text-xl font-bold text-white mb-2">رفع تيمبلت</h3>
              <p className="text-gray-400">ارفع ملف JSON لإنشاء تيمبلت جديد</p>
            </div>
          </Link>

          <Link to="/templates" className="group">
            <div className="bg-gray-800 p-8 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105">
              <div className="text-4xl mb-4">📋</div>
              <h3 className="text-xl font-bold text-white mb-2">التيمبلت</h3>
              <p className="text-gray-400">عرض وإدارة التيمبلت المحفوظة</p>
            </div>
          </Link>

          <Link to="/servers" className="group">
            <div className="bg-gray-800 p-8 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105">
              <div className="text-4xl mb-4">🎮</div>
              <h3 className="text-xl font-bold text-white mb-2">السيرفرات</h3>
              <p className="text-gray-400">عرض السيرفرات المنشأة</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

// Upload Component
const Upload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/json') {
      setFile(selectedFile);
      setMessage('');
    } else {
      setMessage('الرجاء اختيار ملف JSON صحيح');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('الرجاء اختيار ملف');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/templates/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage(`تم رفع التيمبلت بنجاح: ${response.data.template_name}`);
      setFile(null);
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (error) {
      setMessage(`خطأ في رفع الملف: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/json') {
      setFile(droppedFile);
      setMessage('');
    } else {
      setMessage('الرجاء إسقاط ملف JSON صحيح');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-8">
      <div className="container mx-auto max-w-2xl">
        <Link to="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          ← العودة إلى الصفحة الرئيسية
        </Link>
        
        <div className="bg-gray-800 p-8 rounded-xl">
          <h2 className="text-3xl font-bold text-white mb-6 text-center">رفع تيمبلت Discord</h2>
          
          {/* Drag and Drop Area */}
          <div
            className="border-2 border-dashed border-gray-600 p-8 rounded-lg text-center hover:border-blue-400 transition-colors"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <div className="text-4xl mb-4">📁</div>
            <p className="text-gray-300 mb-4">اسحب وأسقط ملف JSON هنا أو</p>
            <input
              id="file-input"
              type="file"
              accept=".json"
              onChange={handleFileChange}
              className="hidden"
            />
            <label
              htmlFor="file-input"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg cursor-pointer hover:bg-blue-700 transition-colors"
            >
              اختر ملف
            </label>
          </div>

          {file && (
            <div className="mt-6 p-4 bg-gray-700 rounded-lg">
              <p className="text-white">
                <strong>الملف المختار:</strong> {file.name}
              </p>
              <p className="text-gray-400">الحجم: {(file.size / 1024).toFixed(2)} KB</p>
            </div>
          )}

          {message && (
            <div className={`mt-6 p-4 rounded-lg ${message.includes('نجاح') || message.includes('بنجاح') ? 'bg-green-800 text-green-200' : 'bg-red-800 text-red-200'}`}>
              {message}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full mt-6 bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'جاري الرفع...' : 'رفع التيمبلت'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Templates Component
const Templates = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [serverName, setServerName] = useState('');
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState('');

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const createServer = async () => {
    if (!selectedTemplate || !serverName.trim()) {
      setMessage('الرجاء اختيار تيمبلت وإدخال اسم السيرفر');
      return;
    }

    setCreating(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/servers/create`, {
        template_id: selectedTemplate.id,
        server_name: serverName.trim()
      });

      if (response.data.success) {
        setMessage(`تم إنشاء السيرفر بنجاح! 🎉`);
        if (response.data.invite_link) {
          setMessage(prev => prev + ` رابط الدعوة: ${response.data.invite_link}`);
        }
        setServerName('');
        setSelectedTemplate(null);
      } else {
        setMessage(`فشل في إنشاء السيرفر: ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`خطأ: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCreating(false);
    }
  };

  const deleteTemplate = async (templateId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا التيمبلت؟')) return;

    try {
      await axios.delete(`${API}/templates/${templateId}`);
      setMessage('تم حذف التيمبلت بنجاح');
      fetchTemplates(); // Refresh the list
    } catch (error) {
      setMessage(`خطأ في حذف التيمبلت: ${error.response?.data?.detail || error.message}`);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center">
        <div className="text-white text-xl">جاري التحميل...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-8">
      <div className="container mx-auto">
        <Link to="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          ← العودة إلى الصفحة الرئيسية
        </Link>

        <h2 className="text-3xl font-bold text-white mb-8 text-center">التيمبلت المحفوظة</h2>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.includes('نجاح') || message.includes('🎉') ? 'bg-green-800 text-green-200' : 'bg-red-800 text-red-200'}`}>
            {message}
          </div>
        )}

        {/* Server Creation Form */}
        {selectedTemplate && (
          <div className="bg-gray-800 p-6 rounded-xl mb-8">
            <h3 className="text-xl font-bold text-white mb-4">إنشاء سيرفر من: {selectedTemplate.name}</h3>
            <div className="flex gap-4">
              <input
                type="text"
                value={serverName}
                onChange={(e) => setServerName(e.target.value)}
                placeholder="اسم السيرفر الجديد"
                className="flex-1 p-3 rounded-lg bg-gray-700 text-white placeholder-gray-400"
              />
              <button
                onClick={createServer}
                disabled={creating}
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-600 transition-colors"
              >
                {creating ? 'جاري الإنشاء...' : 'إنشاء السيرفر'}
              </button>
              <button
                onClick={() => setSelectedTemplate(null)}
                className="bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                إلغاء
              </button>
            </div>
          </div>
        )}

        {templates.length === 0 ? (
          <div className="text-center text-gray-400">
            <div className="text-6xl mb-4">📭</div>
            <p className="text-xl">لا توجد تيمبلت محفوظة</p>
            <Link to="/upload" className="text-blue-400 hover:text-blue-300 mt-4 inline-block">
              ارفع تيمبلت جديد
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div key={template.id} className="bg-gray-800 p-6 rounded-xl">
                <h3 className="text-xl font-bold text-white mb-2">{template.name}</h3>
                {template.description && (
                  <p className="text-gray-400 mb-4">{template.description}</p>
                )}
                
                <div className="text-sm text-gray-300 mb-4">
                  <p>القنوات: {template.channels.length}</p>
                  <p>الأدوار: {template.roles.length}</p>
                  <p>تاريخ الإنشاء: {new Date(template.created_at).toLocaleDateString('ar-SA')}</p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedTemplate(template)}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    إنشاء سيرفر
                  </button>
                  <button
                    onClick={() => deleteTemplate(template.id)}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Servers Component
const Servers = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchServers = async () => {
    try {
      const response = await axios.get(`${API}/servers/created`);
      setServers(response.data);
    } catch (error) {
      console.error('Error fetching servers:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center">
        <div className="text-white text-xl">جاري التحميل...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-8">
      <div className="container mx-auto">
        <Link to="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          ← العودة إلى الصفحة الرئيسية
        </Link>

        <h2 className="text-3xl font-bold text-white mb-8 text-center">السيرفرات المنشأة</h2>

        {servers.length === 0 ? (
          <div className="text-center text-gray-400">
            <div className="text-6xl mb-4">🏗️</div>
            <p className="text-xl">لم يتم إنشاء أي سيرفرات بعد</p>
            <Link to="/templates" className="text-blue-400 hover:text-blue-300 mt-4 inline-block">
              إنشاء سيرفر جديد
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {servers.map((server) => (
              <div key={server.id} className="bg-gray-800 p-6 rounded-xl">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">{server.server_name}</h3>
                    <p className="text-gray-400 mb-2">ID: {server.server_id}</p>
                    <p className="text-gray-400 mb-4">
                      تاريخ الإنشاء: {new Date(server.created_at).toLocaleString('ar-SA')}
                    </p>
                  </div>
                  
                  {server.success && (
                    <div className="bg-green-800 text-green-200 px-3 py-1 rounded-full text-sm">
                      ✅ تم بنجاح
                    </div>
                  )}
                </div>

                {server.invite_link && (
                  <div className="mt-4">
                    <a
                      href={server.invite_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors inline-block"
                    >
                      🔗 انضم للسيرفر
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/servers" element={<Servers />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;