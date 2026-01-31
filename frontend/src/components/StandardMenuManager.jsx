import React, { useState, useEffect } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

import apiClient from '../api/client';

function StandardMenuManager() {
  const [standardMenus, setStandardMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingMenu, setEditingMenu] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    normalized_name: '',
    category: '',
    description: '',
  });

  useEffect(() => {
    fetchStandardMenus();
  }, []);

  const fetchStandardMenus = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/standard-menus/');
      setStandardMenus(response.data.results || response.data);
      setError(null);
    } catch (err) {
      setError('표준 메뉴 목록을 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (menu = null) => {
    if (menu) {
      setEditingMenu(menu);
      setFormData({
        name: menu.name,
        normalized_name: menu.normalized_name,
        category: menu.category || '',
        description: menu.description || '',
      });
    } else {
      setEditingMenu(null);
      setFormData({
        name: '',
        normalized_name: '',
        category: '',
        description: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingMenu(null);
    setFormData({
      name: '',
      normalized_name: '',
      category: '',
      description: '',
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingMenu) {
        await apiClient.put(`/standard-menus/${editingMenu.id}/`, formData);
      } else {
        await apiClient.post('/standard-menus/', formData);
      }
      handleCloseDialog();
      fetchStandardMenus();
    } catch (err) {
      setError(editingMenu ? '표준 메뉴 수정에 실패했습니다.' : '표준 메뉴 추가에 실패했습니다.');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await apiClient.delete(`/standard-menus/${id}/`);
      fetchStandardMenus();
    } catch (err) {
      setError('표준 메뉴 삭제에 실패했습니다.');
      console.error(err);
    }
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
        <Typography variant="h4">표준 메뉴 관리</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          표준 메뉴 추가
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>표준 메뉴명</TableCell>
              <TableCell>정규화명</TableCell>
              <TableCell>카테고리</TableCell>
              <TableCell align="right">매칭 횟수</TableCell>
              <TableCell>상태</TableCell>
              <TableCell align="right">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {standardMenus.map((menu) => (
              <TableRow key={menu.id}>
                <TableCell>{menu.name}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {menu.normalized_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  {menu.category && (
                    <Chip label={menu.category} size="small" />
                  )}
                </TableCell>
                <TableCell align="right">{menu.match_count || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={menu.is_active ? '활성' : '비활성'}
                    size="small"
                    color={menu.is_active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(menu)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(menu.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {standardMenus.length === 0 && (
          <Box p={3} textAlign="center">
            <Typography color="text.secondary">
              등록된 표준 메뉴가 없습니다.
            </Typography>
          </Box>
        )}
      </Paper>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>
            {editingMenu ? '표준 메뉴 수정' : '표준 메뉴 추가'}
          </DialogTitle>
          <DialogContent>
            <TextField
              name="name"
              label="표준 메뉴명"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
              required
              margin="normal"
            />
            <TextField
              name="normalized_name"
              label="정규화명"
              value={formData.normalized_name}
              onChange={handleInputChange}
              fullWidth
              required
              margin="normal"
              helperText="공백, 특수문자 제거된 형태"
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
              name="description"
              label="설명"
              value={formData.description}
              onChange={handleInputChange}
              fullWidth
              margin="normal"
              multiline
              rows={3}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>취소</Button>
            <Button type="submit" variant="contained" color="primary">
              {editingMenu ? '수정' : '추가'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
}

export default StandardMenuManager;
