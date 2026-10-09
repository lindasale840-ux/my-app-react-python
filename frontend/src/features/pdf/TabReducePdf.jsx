import React, { useState } from "react";
import JSZip from "jszip";
import { reducePdfBatchApi } from "../../services/reducePdfService";

const TabReducePdf = () => {
  const [files, setFiles] = useState([]);
  const [dpi, setDpi] = useState(120);
  const [quality, setQuality] = useState(70);
  const [loading, setLoading] = useState(false);
  const [progressText, setProgressText] = useState("");
  const [results, setResults] = useState([]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
      setResults([]);
    }
  };

  const handleReduce = async () => {
    if (files.length === 0) {
      alert("Vui lòng chọn ít nhất 1 file PDF!");
      return;
    }

    setLoading(true);
    setResults([]);

    try {
      // 1. Gọi API nén từng file
      const resList = await reducePdfBatchApi(
        files,
        dpi,
        quality,
        (current, total) => {
          setProgressText(`Đang xử lý file ${current}/${total}...`);
        }
      );

      // Lọc các file xử lý thành công
      const successFiles = resList.filter((res) => res.success);

      if (successFiles.length > 0) {
        // 2. Nếu chỉ có 1 file -> Tải trực tiếp file PDF
        if (successFiles.length === 1) {
          const res = successFiles[0];
          const url = window.URL.createObjectURL(new Blob([res.blob]));
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", res.filename);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
        } else {
          // 3. Nếu có nhiều file -> Đóng gói thành 1 file ZIP
          setProgressText("Đang đóng gói file ZIP...");
          const zip = new JSZip();

          // Thêm từng file PDF đã giảm dung lượng vào file ZIP
          successFiles.forEach((res) => {
            zip.file(res.filename, res.blob);
          });

          // Xuất file ZIP
          const zipBlob = await zip.generateAsync({ type: "blob" });
          const zipUrl = window.URL.createObjectURL(zipBlob);

          const link = document.createElement("a");
          link.href = zipUrl;
          link.setAttribute("download", `Reduced_PDFs_${Date.now()}.zip`);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(zipUrl);
        }
      }

      setResults(resList);
    } catch (err) {
      alert("Lỗi hệ thống khi nén hàng loạt: " + err.message);
    } finally {
      setLoading(false);
      setProgressText("");
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-4 text-gray-800">
        Giảm dung lượng PDF hàng loạt (Rasterize)
      </h2>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Chọn danh sách file PDF:
        </label>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {files.length > 0 && (
          <p className="mt-1 text-xs text-blue-600 font-medium">
            Đã chọn {files.length} file.
          </p>
        )}
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
        disabled={loading || files.length === 0}
        className={`w-full py-2.5 px-4 rounded-md text-white font-medium transition-colors ${
          loading || files.length === 0
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {loading
          ? progressText || "Đang xử lý..."
          : `Thực Hiện Giảm Dung Lượng (${files.length} File)`}
      </button>

      {/* Danh sách báo cáo kết quả */}
      {results.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md text-sm space-y-2 max-h-48 overflow-y-auto">
          <p className="font-bold text-gray-700">Kết quả xử lý:</p>
          {results.map((res, idx) => (
            <div key={idx} className="flex justify-between items-center text-xs border-b pb-1">
              <span className="truncate max-w-[200px] font-medium">{res.filename}</span>
              {res.success ? (
                <span className="text-green-600 font-semibold">
                  ✅ {res.oldSize || 0} MB → {res.newSize || 0} MB
                </span>
              ) : (
                <span className="text-red-600 font-semibold">❌ Lỗi: {res.error}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TabReducePdf;