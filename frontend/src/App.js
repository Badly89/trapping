// frontend/src/App.js - ПОЛНАЯ ВЕРСИЯ С ГЕОЛОКАЦИЕЙ
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container, AppBar, Toolbar, Typography, Paper, List, ListItem,
  ListItemText, Chip, IconButton, Dialog, DialogTitle, DialogContent,
  TextField, Button, Card, CardContent, Badge, Grid,
  Box, CircularProgress, Alert, Snackbar, Divider, Tabs, Tab,
  Tooltip
} from '@mui/material';

import {
  Refresh, CheckCircle, Schedule, AssignmentInd,
  TrendingUp, Today, Speed, Close as CloseIcon,
  LocationOn
} from '@mui/icons-material';

import LocationDisplay from './components/LocationDisplay';

const API_URL = 'http://localhost:5001/api';

// Компонент для отображения галереи фото
function ImageGallery({ photos }) {
  const [open, setOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);

  if (!photos || photos.length === 0) return null;

  return (
    <>
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          📷 Вложения ({photos.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {photos.map((photo, idx) => (
            <Box
              key={idx}
              sx={{
                width: 100,
                height: 100,
                cursor: 'pointer',
                borderRadius: 1,
                overflow: 'hidden',
                border: '1px solid #e0e0e0',
                backgroundColor: '#f5f5f5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                '&:hover': { opacity: 0.8 }
              }}
              onClick={() => {
                setSelectedImage(photo);
                setOpen(true);
              }}
            >
              <img
                src={photo}
                alt={`Фото ${idx + 1}`}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }}
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/100?text=No+image';
                }}
              />
            </Box>
          ))}
        </Box>
      </Box>

      {/* Диалог для просмотра в полном размере */}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="lg"
        PaperProps={{
          sx: {
            backgroundColor: 'transparent',
            boxShadow: 'none',
          }
        }}
      >
        <IconButton
          onClick={() => setOpen(false)}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: 'white',
            backgroundColor: 'rgba(0,0,0,0.5)',
            '&:hover': { backgroundColor: 'rgba(0,0,0,0.7)' },
            zIndex: 1
          }}
        >
          <CloseIcon />
        </IconButton>
        {selectedImage && (
          <img
            src={selectedImage}
            alt="Full size"
            style={{
              maxWidth: '90vw',
              maxHeight: '90vh',
              objectFit: 'contain'
            }}
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/400?text=Image+not+available';
            }}
          />
        )}
      </Dialog>
    </>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [notes, setNotes] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    fetchMessages();
    fetchStatistics();
    const interval = setInterval(() => {
      fetchMessages();
      fetchStatistics();
    }, 30000);
    return () => clearInterval(interval);
  }, [tabValue]);

  const showNotification = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchMessages = async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/messages?limit=200`;
      if (tabValue === 1) url += '&status=new';
      else if (tabValue === 2) url += '&status=processing';
      else if (tabValue === 3) url += '&status=completed';

      const response = await axios.get(url);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
      showNotification('Ошибка загрузки сообщений', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_URL}/statistics`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const updateMessage = async (id, updates) => {
    try {
      const response = await axios.patch(`${API_URL}/messages/${id}`, updates);
      showNotification('Статус обновлен', 'success');
      fetchMessages();
      fetchStatistics();
      if (selectedMessage?.id === id) {
        setSelectedMessage(response.data);
      }
    } catch (error) {
      showNotification('Ошибка обновления', 'error');
    }
  };

  const getStatusColor = (status) => {
    const colors = { new: 'warning', processing: 'info', completed: 'success', cancelled: 'error' };
    return colors[status] || 'default';
  };

  const getStatusText = (status) => {
    const texts = { new: 'Новая', processing: 'В работе', completed: 'Завершена', cancelled: 'Отменена' };
    return texts[status] || status;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата неизвестна';
    
    try {
      const date = new Date(dateString);
      
      if (isNaN(date.getTime())) {
        console.error('Invalid date:', dateString);
        return 'Неверная дата';
      }
      
      const now = new Date();
      const diff = now - date;
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);
      
      if (minutes < 1) return 'Только что';
      if (minutes < 60) return `${minutes} мин назад`;
      if (hours < 24) return `${hours} ч назад`;
      if (days < 7) return `${days} дн назад`;
      
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Ошибка даты';
    }
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            📊 MAX CRM Dashboard
          </Typography>
          {stats && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Tooltip title="Новые сообщения">
                <Badge badgeContent={stats.by_status?.new || 0} color="error">
                  <Schedule />
                </Badge>
              </Tooltip>
              <Tooltip title="В работе">
                <Badge badgeContent={stats.by_status?.processing || 0} color="primary">
                  <AssignmentInd />
                </Badge>
              </Tooltip>
              <Tooltip title="Завершены">
                <Badge badgeContent={stats.by_status?.completed || 0} color="success">
                  <CheckCircle />
                </Badge>
              </Tooltip>
              {stats.messages_with_location > 0 && (
                <Tooltip title={`${stats.messages_with_location} сообщений с геолокацией`}>
                  <Badge badgeContent={stats.messages_with_location} color="info">
                    <LocationOn />
                  </Badge>
                </Tooltip>
              )}
            </Box>
          )}
          <IconButton color="inherit" onClick={() => { fetchMessages(); fetchStatistics(); }}>
            <Refresh />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ marginTop: 2, marginBottom: 2 }}>
        {/* Статистика */}
        {stats && (
          <Grid container spacing={2} sx={{ marginBottom: 2 }}>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUp color="action" />
                    <Typography variant="body2" color="textSecondary">
                      Всего обращений
                    </Typography>
                  </Box>
                  <Typography variant="h4">{stats.total || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Today color="action" />
                    <Typography variant="body2" color="textSecondary">
                      За сегодня
                    </Typography>
                  </Box>
                  <Typography variant="h4">{stats.messages_today || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Speed color="action" />
                    <Typography variant="body2" color="textSecondary">
                      В работе
                    </Typography>
                  </Box>
                  <Typography variant="h4">{stats.by_status?.processing || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocationOn color="action" />
                    <Typography variant="body2" color="textSecondary">
                      С геолокацией
                    </Typography>
                  </Box>
                  <Typography variant="h4">{stats.messages_with_location || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Табы фильтрации */}
        <Paper sx={{ marginBottom: 2 }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Все" />
            <Tab label="Новые" />
            <Tab label="В работе" />
            <Tab label="Завершены" />
          </Tabs>
        </Paper>

        {/* Список сообщений */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 7 }}>
            <Paper sx={{ maxHeight: '70vh', overflow: 'auto' }}>
              {loading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <List>
                  {messages.map((msg) => (
                    <React.Fragment key={msg.id}>
                      <ListItem
                        component="div"
                        onClick={() => {
                          setSelectedMessage(msg);
                          setNotes(msg.notes || '');
                          setDialogOpen(true);
                        }}
                        sx={{
                          cursor: 'pointer',
                          '&:hover': { bgcolor: 'action.hover' },
                          flexDirection: 'column',
                          alignItems: 'flex-start'
                        }}
                      >
                        <ListItemText
                          primary={
                            <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                              <Typography component="span" variant="body1" fontWeight="bold">
                                {msg.user_name}
                              </Typography>
                              <Chip
                                label={getStatusText(msg.status)}
                                size="small"
                                color={getStatusColor(msg.status)}
                              />
                              <Tooltip title={new Date(msg.created_at).toLocaleString('ru-RU')}>
                                <Chip
                                  label={formatDate(msg.created_at)}
                                  size="small"
                                  variant="outlined"
                                />
                              </Tooltip>
                              {msg.latitude && msg.longitude && (
                                <Chip
                                  icon={<LocationOn />}
                                  label="Геолокация"
                                  size="small"
                                  color="info"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box component="span" sx={{ display: 'block', mt: 1 }}>
                              <Typography component="span" variant="body2" color="textPrimary">
                                {msg.text?.substring(0, 100) || 'Нет текста'}
                              </Typography>
                              
                              {/* Геолокация в списке сообщений */}
                              {msg.latitude && msg.longitude && (
                                <Box component="span" sx={{ display: 'block', mt: 0.5 }}>
                                  <Typography component="span" variant="caption" color="textSecondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <LocationOn fontSize="inherit" />
                                    📍 {msg.latitude.toFixed(4)}, {msg.longitude.toFixed(4)}
                                  </Typography>
                                </Box>
                              )}
                              
                              {msg.photos?.length > 0 && (
                                <Box component="span" sx={{ display: 'block', mt: 0.5 }}>
                                  <Typography component="span" variant="caption" color="textSecondary">
                                    📷 {msg.photos.length} фото
                                  </Typography>
                                </Box>
                              )}
                              {msg.notes && (
                                <Box component="span" sx={{ display: 'block', mt: 0.5 }}>
                                  <Typography component="span" variant="caption" color="textSecondary">
                                    📝 {msg.notes.substring(0, 50)}
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                  {messages.length === 0 && !loading && (
                    <Box p={4} textAlign="center">
                      <Typography color="textSecondary">
                        Нет сообщений для отображения
                      </Typography>
                    </Box>
                  )}
                </List>
              )}
            </Paper>
          </Grid>

          {/* Быстрая статистика */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Paper sx={{ padding: 2 }}>
              <Typography variant="h6" gutterBottom>
                📈 Распределение по статусам
              </Typography>
              {stats && (
                <Grid container spacing={2}>
                  <Grid size={{ xs: 6 }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="textSecondary">
                          Новые
                        </Typography>
                        <Typography variant="h5" color="warning.main">
                          {stats.by_status?.new || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="textSecondary">
                          В работе
                        </Typography>
                        <Typography variant="h5" color="primary.main">
                          {stats.by_status?.processing || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="textSecondary">
                          Завершены
                        </Typography>
                        <Typography variant="h5" color="success.main">
                          {stats.by_status?.completed || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="textSecondary">
                          Отменены
                        </Typography>
                        <Typography variant="h5" color="error.main">
                          {stats.by_status?.cancelled || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Диалог редактирования сообщения с фото и геолокацией */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          {selectedMessage && (
            <>
              <DialogTitle>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">
                    Сообщение от {selectedMessage.user_name}
                  </Typography>
                  <Chip label={`ID: ${selectedMessage.id}`} size="small" variant="outlined" />
                </Box>
              </DialogTitle>
              <DialogContent>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    📅 {new Date(selectedMessage.created_at).toLocaleString('ru-RU')}
                  </Typography>
                </Box>

                <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                  {selectedMessage.text || 'Нет текста'}
                </Typography>

                {/* Геолокация в диалоге */}
                {selectedMessage.latitude && selectedMessage.longitude && (
                  <LocationDisplay 
                    latitude={selectedMessage.latitude}
                    longitude={selectedMessage.longitude}
                  />
                )}

                {/* Галерея фото */}
                <ImageGallery photos={selectedMessage.photos} />

                <Divider sx={{ my: 2 }} />

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Действия:
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    <Button
                      variant="contained"
                      color="warning"
                      onClick={() => updateMessage(selectedMessage.id, { status: 'new' })}
                    >
                      В новые
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => updateMessage(selectedMessage.id, { status: 'processing' })}
                    >
                      В работу
                    </Button>
                    <Button
                      variant="contained"
                      color="success"
                      onClick={() => updateMessage(selectedMessage.id, { status: 'completed' })}
                    >
                      Завершить
                    </Button>
                  </Box>
                </Box>

                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Заметки менеджера"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
                <Button
                  variant="outlined"
                  onClick={() => updateMessage(selectedMessage.id, { notes })}
                  sx={{ mt: 1 }}
                >
                  💾 Сохранить заметки
                </Button>
              </DialogContent>
            </>
          )}
        </Dialog>

        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            severity={snackbar.severity}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
}

export default App;