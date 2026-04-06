// frontend/src/components/LocationDisplay.js
import React from 'react';
import { Box, Typography, Chip, Button } from '@mui/material';
import { LocationOn, Map, OpenInNew } from '@mui/icons-material';

export default function LocationDisplay({ latitude, longitude }) {
  if (!latitude || !longitude) return null;

  // Формируем ссылки на карты
  const mapsLinks = {
    yandex: `https://yandex.ru/maps/?pt=${longitude},${latitude}&z=17&l=map`,
    google: `https://www.google.com/maps?q=${latitude},${longitude}`,
    openstreetmap: `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=17/${latitude}/${longitude}`
  };

  return (
    <Box sx={{ mt: 2, p: 1.5, bgcolor: '#f5f5f5', borderRadius: 1 }}>
      <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
        <LocationOn fontSize="small" color="primary" />
        📍 Геолокация:
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Chip
          size="small"
          label={`${latitude.toFixed(6)}° с.ш.`}
          variant="outlined"
        />
        <Chip
          size="small"
          label={`${longitude.toFixed(6)}° в.д.`}
          variant="outlined"
        />
      </Box>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Button
          size="small"
          variant="outlined"
          startIcon={<Map />}
          component="a"
          href={mapsLinks.yandex}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ textTransform: 'none' }}
        >
          Яндекс.Карты
        </Button>
        <Button
          size="small"
          variant="outlined"
          startIcon={<OpenInNew />}
          component="a"
          href={mapsLinks.google}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ textTransform: 'none' }}
        >
          Google Maps
        </Button>
        <Button
          size="small"
          variant="outlined"
          startIcon={<OpenInNew />}
          component="a"
          href={mapsLinks.openstreetmap}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ textTransform: 'none' }}
        >
          OpenStreetMap
        </Button>
      </Box>
    </Box>
  );
}