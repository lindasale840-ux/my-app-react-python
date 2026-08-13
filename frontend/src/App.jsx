import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import PdfToolsPage from './pages/PdfToolsPage';
import PDFSPLIT from './pages/PDFSPLIT';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* Page 1: Trang xử lý PDF */}
          <Route path="/" element={<PdfToolsPage />} />
          {/* Page 2: Trang xử lý PDF */}
          <Route path="/split" element={<PDFSPLIT />} />

          {/* Các Page lớn còn lại (Chưa làm thì hiện chữ giữ chỗ) */}
          <Route path="/excel" element={<h2>Trang 2: Xử lý Excel (Sắp làm)</h2>} />
          <Route path="/page-3" element={<h2>Trang 3 (Sắp làm)</h2>} />
          <Route path="/page-4" element={<h2>Trang 4 (Sắp làm)</h2>} />
          <Route path="/page-5" element={<h2>Trang 5 (Sắp làm)</h2>} />
          <Route path="/page-6" element={<h2>Trang 6 (Sắp làm)</h2>} />
          <Route path="/page-7" element={<h2>Trang 7 (Sắp làm)</h2>} />
          <Route path="/page-8" element={<h2>Trang 8 (Sắp làm)</h2>} />
          <Route path="/page-9" element={<h2>Trang 9 (Sắp làm)</h2>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}