#include "capture.hpp"
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

    Size size = { width, height };
    CaptureWindowOutput output = { size, buffer };
    return output;
};

CaptureWindowOutput captureWindowWinRT(uint64_t _window)
{
    HWND window = (HWND)_window;
    using namespace winrt::Windows::Graphics::Capture;
    using namespace winrt::Windows::Foundation;
    using namespace winrt::Windows::Graphics::DirectX;
    using namespace winrt::Windows::Graphics::DirectX::Direct3D11;
    using namespace winrt::Windows::Graphics::Imaging;
    using Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess;
    using winrt::check_hresult;
    using winrt::Windows::Graphics::SizeInt32;
    // Create capture item
    try
    {
        GraphicsCaptureItem item(nullptr);
        auto activation_factory = winrt::get_activation_factory<GraphicsCaptureItem>();
        auto interop_factory = activation_factory.as<IGraphicsCaptureItemInterop>();
        check_hresult(interop_factory->CreateForWindow(
            window,
            winrt::guid_of<IGraphicsCaptureItem>(),
            reinterpret_cast<void**>(winrt::put_abi(item)) /*output*/
        ));

        winrt::com_ptr<ID3D11Device> d3d_device;
        // https://docs.microsoft.com/en-us/windows/win32/api/d3d11/nf-d3d11-d3d11createdevice
        check_hresult(D3D11CreateDevice(
            nullptr,
            D3D_DRIVER_TYPE_HARDWARE,
            nullptr,
            0,    /*createDeviceFlags*/
            NULL, /*featureLevels*/
            0,
            D3D11_SDK_VERSION,
            d3d_device.put(), /*output*/
            NULL,
            NULL));

        auto idxgDevice = d3d_device.as<IDXGIDevice>();
        // check_hresult(d3d_device->QueryInterface(__uuidof(IDXGIDevice), idxgDevice.put() /* output */));
        winrt::com_ptr<::IInspectable> inspectable;
        check_hresult(CreateDirect3D11DeviceFromDXGIDevice(idxgDevice.get(), inspectable.put() /* output */));
        const IDirect3DDevice device = inspectable.as<IDirect3DDevice>();
        Direct3D11CaptureFramePool framePool = Direct3D11CaptureFramePool::Create(
            device,
            DirectXPixelFormat::B8G8R8A8UIntNormalized,
            1,          // capture 1 frame
            item.Size() // size of buffer
        );
        GraphicsCaptureSession session = framePool.CreateCaptureSession(item);
        session.IsCursorCaptureEnabled(false);
        std::vector<byte> buffer;
        ::Size size{ 0,0 };
        unsigned frame_count = 0;
        framePool.FrameArrived(
            [&](Direct3D11CaptureFramePool const& pool, auto&) -> IAsyncOperation<uint8_t>
            {
                if (frame_count >= 1) { co_return 0; }
                Direct3D11CaptureFrame frame = pool.TryGetNextFrame();
                SoftwareBitmap bitmap = co_await SoftwareBitmap::CreateCopyFromSurfaceAsync(frame.Surface());
                size.width = bitmap.PixelWidth();
                size.height = bitmap.PixelHeight();
                winrt::Windows::Storage::Streams::Buffer bitmapBuffer(sizeof(UINT32) * size.width * size.height);
                bitmap.CopyToBuffer(bitmapBuffer);
                buffer.resize(bitmapBuffer.Length());
                std::copy(bitmapBuffer.data(), bitmapBuffer.data() + bitmapBuffer.Length(), buffer.data());
                frame_count++;
                co_return 0;
            }
        );
        session.StartCapture();

        // Message pump
        MSG message;
        while (frame_count < 1)
        {
            if (GetMessage(&message, nullptr, 0, 0) > 0)
            {
                DispatchMessage(&message);
            }
        }

        CaptureWindowOutput output = { size, buffer };
        return output;
    }
    catch (const std::exception& anything)
    {
        std::cerr << anything.what() << std::endl;
    }
    catch (winrt::hresult_error const& ex)
    {
        winrt::hresult hr = ex.code();         // HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND).
        winrt::hstring message = ex.message(); // The system cannot find the file specified.
        std::cerr << hr << std::endl;
        std::wcerr << message.c_str() << std::endl;
    }
}
