import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import { Link as RouterLink } from 'react-router-dom';

import theme from './theme';
import RestaurantList from './components/RestaurantList';
import RestaurantDetail from './components/RestaurantDetail';
import MatchedMenusView from './components/MatchedMenusView';
import StandardMenuManager from './components/StandardMenuManager';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                표준 메뉴 매칭 서비스
              </Typography>
              <Button color="inherit" component={RouterLink} to="/restaurants">
                레스토랑
              </Button>
              <Button color="inherit" component={RouterLink} to="/matched-menus">
                매칭된 메뉴
              </Button>
              <Button color="inherit" component={RouterLink} to="/standard-menus">
                표준 메뉴 관리
              </Button>
            </Toolbar>
          </AppBar>

          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Routes>
              <Route path="/" element={<Navigate to="/restaurants" replace />} />
              <Route path="/restaurants" element={<RestaurantList />} />
              <Route path="/restaurants/:id" element={<RestaurantDetail />} />
              <Route path="/matched-menus" element={<MatchedMenusView />} />
              <Route path="/standard-menus" element={<StandardMenuManager />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
