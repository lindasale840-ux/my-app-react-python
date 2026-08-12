import React, { useState } from "react";
// Import chuẩn từ thư mục services
import { reducePdfApi } from "../../services/reducePdfService";

const TabReducePdf = () => {
  const [file, setFile] = useState(null);
  const [dpi, setDpi] = useState(120);
  const [quality, setQuality] = useState(70);
  const [loading, setLoading] = useState(false);
  const [resultInfo, setResultInfo] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResultInfo(null);
    }
  };

  const handleReduce = async () => {
    if (!file) {
      alert("Vui lòng chọn 1 file PDF!");
      return;
    }

    setLoading(true);
    setResultInfo(null);

    try {
      const res = await reducePdfApi(file, dpi, quality);

      // Tự động tải file về
      const url = window.URL.createObjectURL(new Blob([res.blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `reduced_${file.name}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setResultInfo({
        message: `✅ Thành công: ${res.oldSize || 0} MB → ${res.newSize || 0} MB`,
      });
    } catch (err) {
      alert("Lỗi khi giảm dung lượng PDF: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-4 text-gray-800">
        Giảm dung lượng PDF (Rasterize)
      </h2>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Chọn file PDF:
        </label>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chất lượng DPI (Mặc định 120):
          </label>
          <input
            type="number"
            value={dpi}
            onChange={(e) => setDpi(Number(e.target.value))}
            className="w-full border rounded p-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chất lượng JPEG (Mặc định 70%):
          </label>
          <input
            type="number"
            value={quality}
            onChange={(e) => setQuality(Number(e.target.value))}
            className="w-full border rounded p-2 text-sm"
          />
        </div>
      </div>

      <button
        onClick={handleReduce}
        disabled={loading || !file}
        className={`w-full py-2.5 px-4 rounded-md text-white font-medium transition-colors ${
          loading || !file
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {loading ? "Đang xử lý giảm dung lượng..." : "Thực Hiện Giảm Dung Lượng"}
      </button>

      {resultInfo && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md font-medium text-center">
          {resultInfo.message}
        </div>
      )}
    </div>
  );
};

export default TabReducePdf;