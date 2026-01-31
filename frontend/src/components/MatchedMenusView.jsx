import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Restaurant as RestaurantIcon,
} from '@mui/icons-material';

import apiClient from '../api/client';

function MatchedMenusView() {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMatchedMenus();
  }, []);

  const fetchMatchedMenus = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/items/?standard_menu__isnull=false');
      const menusData = response.data.results || response.data;

      // 표준 메뉴별로 그룹화
      const grouped = menusData.reduce((acc, menu) => {
        if (!menu.standard_menu_detail) return acc;

        const standardMenuId = menu.standard_menu_detail.id;
        if (!acc[standardMenuId]) {
          acc[standardMenuId] = {
            standardMenu: menu.standard_menu_detail,
            menus: [],
          };
        }
        acc[standardMenuId].menus.push(menu);
        return acc;
      }, {});

      setMenus(Object.values(grouped));
      setError(null);
    } catch (err) {
      setError('매칭된 메뉴 목록을 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
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
      <Typography variant="h4" gutterBottom>
        매칭된 메뉴
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {menus.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">
            매칭된 메뉴가 없습니다.
          </Typography>
        </Paper>
      ) : (
        <Box>
          {menus.map((group) => (
            <Accordion key={group.standardMenu.id}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2} width="100%">
                  <Typography variant="h6">
                    {group.standardMenu.name}
                  </Typography>
                  {group.standardMenu.category && (
                    <Chip label={group.standardMenu.category} size="small" />
                  )}
                  <Chip
                    label={`${group.menus.length}개 메뉴`}
                    size="small"
                    color="primary"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>레스토랑</TableCell>
                      <TableCell>원본 메뉴명</TableCell>
                      <TableCell align="right">가격</TableCell>
                      <TableCell align="right">신뢰도</TableCell>
                      <TableCell>매칭 방법</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {group.menus.map((menu) => (
                      <TableRow key={menu.id}>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <RestaurantIcon fontSize="small" color="action" />
                            {menu.restaurant_detail?.name || menu.restaurant_code}
                          </Box>
                        </TableCell>
                        <TableCell>{menu.original_name}</TableCell>
                        <TableCell align="right">
                          {menu.price ? `${menu.price.toLocaleString()}원` : '-'}
                        </TableCell>
                        <TableCell align="right">
                          {menu.match_confidence
                            ? `${(menu.match_confidence * 100).toFixed(0)}%`
                            : '-'}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={menu.match_method}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </div>
  );
}

export default MatchedMenusView;
