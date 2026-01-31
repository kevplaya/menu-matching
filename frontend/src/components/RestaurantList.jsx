import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Box,
  Chip,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Add as AddIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';

import apiClient from '../api/client';

function RestaurantList() {
  const navigate = useNavigate();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    category: '',
  });

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/restaurants/');
      setRestaurants(response.data.results || response.data);
      setError(null);
    } catch (err) {
      setError('레스토랑 목록을 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setFormData({ name: '', address: '', phone: '', category: '' });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/restaurants/', formData);
      handleCloseDialog();
      fetchRestaurants();
    } catch (err) {
      setError('레스토랑 추가에 실패했습니다.');
      console.error(err);
    }
  };

  const handleCardClick = (id) => {
    navigate(`/restaurants/${id}`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          레스토랑 목록
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
        >
          레스토랑 추가
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {restaurants.map((restaurant) => (
          <Grid item xs={12} sm={6} md={4} key={restaurant.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 6,
                },
              }}
              onClick={() => handleCardClick(restaurant.id)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" mb={1}>
                  <RestaurantIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" component="div">
                    {restaurant.name}
                  </Typography>
                </Box>

                {restaurant.category && (
                  <Chip label={restaurant.category} size="small" sx={{ mb: 1 }} />
                )}

                {restaurant.address && (
                  <Box display="flex" alignItems="center" mt={1}>
                    <LocationIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {restaurant.address}
                    </Typography>
                  </Box>
                )}

                {restaurant.phone && (
                  <Box display="flex" alignItems="center" mt={0.5}>
                    <PhoneIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {restaurant.phone}
                    </Typography>
                  </Box>
                )}
              </CardContent>

              <CardActions>
                <Typography variant="body2" color="text.secondary">
                  메뉴 {restaurant.menu_count || 0}개
                </Typography>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {restaurants.length === 0 && !loading && (
        <Box textAlign="center" mt={4}>
          <Typography color="text.secondary">등록된 레스토랑이 없습니다.</Typography>
        </Box>
      )}

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>레스토랑 추가</DialogTitle>
          <DialogContent>
            <TextField
              name="name"
              label="레스토랑 이름"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
              required
              margin="normal"
            />
            <TextField
              name="category"
              label="카테고리"
              value={formData.category}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
              placeholder="한식, 중식, 일식 등"
            />
            <TextField
              name="address"
              label="주소"
              value={formData.address}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
              multiline
              rows={2}
            />
            <TextField
              name="phone"
              label="전화번호"
              value={formData.phone}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>취소</Button>
            <Button type="submit" variant="contained" color="primary">
              추가
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
}

export default RestaurantList;
