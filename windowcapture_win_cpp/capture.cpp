#include "capture.hpp"
#include "capture_winrt.hpp"
#include "semaphore.hpp"
#include <cassert>
#include <windows.h>
#include <windows.graphics.capture.interop.h>
#include <windows.graphics.directx.direct3d11.interop.h>
#include <windows.graphics.directx.direct3d11.h>
#include <windows.foundation.h>
#include <windows.foundation.metadata.h>
#include <windows.foundation.collections.h>
#include <windows.graphics.h>
#include <windows.graphics.imaging.h>
#include <windows.storage.streams.h>
// #include <wrl/client.h>
#include <windows.graphics.capture.h>
#include <windows.system.h>
#include <inspectable.h>
#include <dxgi.h>
#include <typeinfo>
#include <stdexcept>
#include <d3d11.h>
#include <iostream>
#include <vector>

CaptureWindowOutput captureWindowBitBlt(uint64_t window)
{
    RECT rect = { 0 };
    DPI_AWARENESS_CONTEXT dpiContext = GetWindowDpiAwarenessContext((HWND)window);
    SetProcessDpiAwarenessContext(dpiContext);
    GetClientRect((HWND)window, &rect);
    HDC hdcSrc = GetDC((HWND)window);
    // UINT dpi = GetDpiForWindow((HWND)window) / 96;
    UINT dpi = 1;
    int height = (rect.bottom - rect.top) * dpi;
    int width = (rect.right - rect.left) * dpi;
    if (!dpi)
    {
        std::cerr << "dpi failed" << std::endl;
        abort();
    }
    std::cerr << "dpi = " << dpi << std::endl;
    if (!hdcSrc)
    {
        std::cerr << "hdcSrc failed" << std::endl;
        abort();
    }
    HDC hdcDest = CreateCompatibleDC(hdcSrc);
    if (!hdcDest)
    {
        std::cerr << "hdcDest failed" << std::endl;
        abort();
    }
    HBITMAP hBitmap = CreateCompatibleBitmap(hdcSrc, width, height);
    if (!hBitmap)
    {
        std::cerr << "hBitmap failed" << std::endl;
        abort();
    }
    SelectObject(hdcDest, hBitmap);
    // See https://docs.microsoft.com/en-us/windows/win32/gdi/capturing-an-image
    if (!BitBlt(hdcDest, 0, 0, width, height, hdcSrc, 0, 0, SRCCOPY))
    {
        std::cerr << "BitBlt failed" << std::endl;
        abort();
    }
    // https://docs.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapinfo
    BITMAPINFO info = { 0 };
    info.bmiHeader.biSize = sizeof(info.bmiHeader);
    // Get the BITMAPINFO structure from the bitmap
    if (!GetDIBits(hdcDest, hBitmap, 0, 0, nullptr, &info, DIB_RGB_COLORS))
    {
        std::cerr << "GetDIBits 1 failed" << std::endl;
        abort();
    }
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    /* Flip image up side down, See https://stackoverflow.com/questions/9022784/bitblt-drawing-bitmap-upside-down */
    info.bmiHeader.biHeight = -info.bmiHeader.biHeight;
    std::vector<byte> buffer(info.bmiHeader.biSizeImage, 0);
    // See https://docs.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getdibits
    if (!GetDIBits(hdcDest, hBitmap, 0, info.bmiHeader.biHeight, buffer.data(), &info, DIB_RGB_COLORS))
    {
        std::cerr << "GetDIBits 2 failed" << std::endl;
        abort();
    }
    DeleteDC(hdcDest);
    ReleaseDC(NULL, hdcSrc);

    ::Size size = { width, height };
    CaptureWindowOutput output;
    output.size = size;
    output.frame = buffer;
    return output;
};

CaptureWindowOutput captureWindowWinRT(uint64_t _window)
{
    HWND window = (HWND)_window;
    try
    {
        return CaptureWinRT::instance.startCapture(window);
    }
    catch (const std::exception& anything)
    {
        std::cerr << anything.what() << std::endl;
        throw anything;
    }
    catch (winrt::hresult_error const& ex)
    {
        winrt::hresult hr = ex.code();         // HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND).
        winrt::hstring message = ex.message(); // The system cannot find the file specified.
        std::cerr << hr << std::endl;
        std::wcerr << message.c_str() << std::endl;
        throw ex;
    }
}
