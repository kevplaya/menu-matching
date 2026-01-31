import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

import apiClient from '../api/client';
import MenuMatchingDialog from './MenuMatchingDialog';

function RestaurantDetail() {
  const { id } = useParams();
  const [restaurant, setRestaurant] = useState(null);
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedMenu, setSelectedMenu] = useState(null);
  const [formData, setFormData] = useState({
    original_name: '',
    price: '',
    description: '',
  });

  useEffect(() => {
    fetchRestaurantData();
  }, [id]);

  const fetchRestaurantData = async () => {
    try {
      setLoading(true);
      const [restaurantRes, menusRes] = await Promise.all([
        apiClient.get(`/restaurants/${id}/`),
        apiClient.get(`/restaurants/${id}/menus/`),
      ]);
      setRestaurant(restaurantRes.data);
      setMenus(menusRes.data);
      setError(null);
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
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
    setFormData({ original_name: '', price: '', description: '' });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/items/', {
        ...formData,
        restaurant: parseInt(id),
        price: formData.price ? parseInt(formData.price) : null,
      });
      handleCloseDialog();
      setSelectedMenu(response.data);
      fetchRestaurantData();
    } catch (err) {
      setError('메뉴 추가에 실패했습니다.');
      console.error(err);
    }
  };

  const handleMenuMatchingClose = () => {
    setSelectedMenu(null);
    fetchRestaurantData();
  };

  const getMatchStatusIcon = (menu) => {
    if (!menu.standard_menu) {
      return <ErrorIcon color="error" />;
    }
    const confidence = menu.match_confidence || 0;
    if (confidence >= 0.9) {
      return <CheckCircleIcon color="success" />;
    }
    return <CheckCircleIcon color="warning" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (!restaurant) {
    return (
      <Alert severity="error">레스토랑을 찾을 수 없습니다.</Alert>
    );
  }

  return (
    <div>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {restaurant.name}
        </Typography>
        {restaurant.category && (
          <Chip label={restaurant.category} sx={{ mb: 2 }} />
        )}
        {restaurant.address && (
          <Typography color="text.secondary">주소: {restaurant.address}</Typography>
        )}
        {restaurant.phone && (
          <Typography color="text.secondary">전화: {restaurant.phone}</Typography>
        )}
      </Paper>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">메뉴 목록</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
        >
          메뉴 추가
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <List>
          {menus.map((menu, index) => (
            <React.Fragment key={menu.id}>
              {index > 0 && <Divider />}
              <ListItem
                secondaryAction={
                  <IconButton edge="end" onClick={() => setSelectedMenu(menu)}>
                    <EditIcon />
                  </IconButton>
                }
              >
                <Box sx={{ mr: 2 }}>{getMatchStatusIcon(menu)}</Box>
                <ListItemText
                  primary={menu.original_name}
                  secondary={
                    <Box>
                      {menu.price && (
                        <Typography component="span" variant="body2">
                          {menu.price.toLocaleString()}원
                        </Typography>
                      )}
                      {menu.standard_menu_detail && (
                        <Chip
                          label={`→ ${menu.standard_menu_detail.name}`}
                          size="small"
                          sx={{ ml: 1 }}
                          color={menu.match_confidence >= 0.9 ? 'success' : 'warning'}
                        />
                      )}
                      {menu.match_confidence && (
                        <Typography component="span" variant="caption" sx={{ ml: 1 }}>
                          (신뢰도: {(menu.match_confidence * 100).toFixed(0)}%)
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
        {menus.length === 0 && (
          <Box p={3} textAlign="center">
            <Typography color="text.secondary">등록된 메뉴가 없습니다.</Typography>
          </Box>
        )}
      </Paper>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>메뉴 추가</DialogTitle>
          <DialogContent>
            <TextField
              name="original_name"
              label="메뉴 이름"
              value={formData.original_name}
              onChange={handleInputChange}
              fullWidth
              required
              margin="normal"
            />
            <TextField
              name="price"
              label="가격"
              value={formData.price}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
              type="number"
            />
            <TextField
              name="description"
              label="설명"
              value={formData.description}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
              multiline
              rows={2}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>취소</Button>
            <Button type="submit" variant="contained" color="primary">
              추가 (자동 매칭)
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {selectedMenu && (
        <MenuMatchingDialog
          menu={selectedMenu}
          open={Boolean(selectedMenu)}
          onClose={handleMenuMatchingClose}
        />
      )}
    </div>
  );
}

export default RestaurantDetail;
