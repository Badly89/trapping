// frontend/src/components/PhotoWithProxy.js
import React, { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';

const API_URL = 'http://localhost:5001/api';

function PhotoWithProxy({ photoUrl, messageId, photoIndex, alt, style, onClick }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const loadPhoto = async () => {
      try {
        // Если photoUrl уже является полным URL (начинается с http)
        if (photoUrl && (photoUrl.startsWith('http://') || photoUrl.startsWith('https://'))) {
          // Проверяем, не наш ли это эндпоинт
          if (photoUrl.includes('/api/photos/')) {
            setImageUrl(photoUrl);
          } else {
            // Для внешних URL используем прокси
            const token = photoUrl.split('/').pop();
            const proxyUrl = `${API_URL}/photos/proxy?token=${encodeURIComponent(token)}`;
            setImageUrl(proxyUrl);
          }
        } 
        // Если это локальный URL (начинается с /api/photos/local/)
        else if (photoUrl && photoUrl.startsWith('/api/photos/local/')) {
          setImageUrl(`http://localhost:5001${photoUrl}`);
        }
        // Если есть messageId и photoIndex, используем старый эндпоинт
        else if (messageId !== undefined && photoIndex !== undefined) {
          setImageUrl(`http://localhost:5001/api/photos/${messageId}/${photoIndex}`);
        }
        // Если ничего не подошло
        else {
          console.warn('Не удалось определить URL фото:', photoUrl);
          setError(true);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error loading photo:', err);
        setError(true);
        setLoading(false);
      }
    };

    if (photoUrl) {
      loadPhoto();
    } else {
      setError(true);
      setLoading(false);
    }
  }, [photoUrl, messageId, photoIndex]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', ...style }}>
        <CircularProgress size={30} />
      </Box>
    );
  }

  if (error || !imageUrl) {
    return (
      <img
        src="https://thumbs.dreamstime.com/b/no-image-vector-symbol-missing-available-icon-gallery-moment-placeholder-248305496.jpg"
        alt={alt || "No image"}
        style={style}
        onClick={onClick}
      />
    );
  }

  return (
    <img
      src={imageUrl}
      alt={alt}
      style={style}
      onClick={onClick}
      onError={() => setError(true)}
    />
  );
}

export default PhotoWithProxy;