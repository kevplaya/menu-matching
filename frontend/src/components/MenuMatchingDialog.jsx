import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Alert,
  Autocomplete,
  TextField,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import apiClient from '../api/client';

function MenuMatchingDialog({ menu, open, onClose }) {
  const [standardMenus, setStandardMenus] = useState([]);
  const [selectedStandardMenu, setSelectedStandardMenu] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      fetchStandardMenus();
      if (menu.standard_menu) {
        setSelectedStandardMenu(menu.standard_menu);
      }
    }
  }, [open, menu]);

  const fetchStandardMenus = async () => {
    try {
      const response = await apiClient.get('/standard-menus/');
      setStandardMenus(response.data.results || response.data);
    } catch (err) {
      console.error('표준 메뉴 목록 로드 실패:', err);
    }
  };

  const handleManualMatch = async () => {
    if (!selectedStandardMenu) return;

    try {
      setLoading(true);
      await apiClient.patch(`/items/${menu.id}/`, {
        standard_menu: selectedStandardMenu,
        match_method: 'manual',
        match_confidence: 1.0,
        is_verified: true,
      });
      onClose();
    } catch (err) {
      setError('수동 매칭에 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getMatchStatus = () => {
    if (!menu.standard_menu) {
      return {
        icon: <ErrorIcon color="error" fontSize="large" />,
        color: 'error',
        title: '매칭 실패',
        message: '표준 메뉴를 찾지 못했습니다. 수동으로 매칭해주세요.',
      };
    }

    const confidence = menu.match_confidence || 0;
    if (confidence >= 0.9) {
      return {
        icon: <CheckCircleIcon color="success" fontSize="large" />,
        color: 'success',
        title: '매칭 성공',
        message: '높은 신뢰도로 매칭되었습니다.',
      };
    }

    return {
      icon: <WarningIcon color="warning" fontSize="large" />,
      color: 'warning',
      title: '낮은 신뢰도',
      message: '매칭 신뢰도가 낮습니다. 확인 후 수동 매칭을 권장합니다.',
    };
  };

  const status = getMatchStatus();

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>메뉴 매칭 결과</DialogTitle>
      <DialogContent>
        <Box textAlign="center" mb={3}>
          {status.icon}
          <Typography variant="h6" mt={1}>
            {status.title}
          </Typography>
          <Typography color="text.secondary" variant="body2">
            {status.message}
          </Typography>
        </Box>

        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            원본 메뉴명
          </Typography>
          <Typography variant="body1" fontWeight="bold">
            {menu.original_name}
          </Typography>
        </Box>

        {menu.standard_menu_detail && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              매칭된 표준 메뉴
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body1" fontWeight="bold">
                {menu.standard_menu_detail.name}
              </Typography>
              {menu.standard_menu_detail.category && (
                <Chip label={menu.standard_menu_detail.category} size="small" />
              )}
            </Box>
          </Box>
        )}

        {menu.match_confidence && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              매칭 정보
            </Typography>
            <Typography variant="body2">
              신뢰도: {(menu.match_confidence * 100).toFixed(1)}%
            </Typography>
            <Typography variant="body2">
              매칭 방법: {menu.match_method}
            </Typography>
          </Box>
        )}

        <Box mt={3}>
          <Typography variant="subtitle2" gutterBottom>
            수동 매칭
          </Typography>
          <Autocomplete
            options={standardMenus}
            getOptionLabel={(option) =>
              `${option.name}${option.category ? ` (${option.category})` : ''}`
            }
            value={
              standardMenus.find((sm) => sm.id === selectedStandardMenu) || null
            }
            onChange={(_, newValue) => {
              setSelectedStandardMenu(newValue ? newValue.id : null);
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="표준 메뉴 선택"
                placeholder="표준 메뉴를 검색하세요"
              />
            )}
          />
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>닫기</Button>
        {selectedStandardMenu !== menu.standard_menu && (
          <Button
            variant="contained"
            color="primary"
            onClick={handleManualMatch}
            disabled={loading || !selectedStandardMenu}
          >
            {loading ? <CircularProgress size={24} /> : '수동 매칭'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

export default MenuMatchingDialog;
