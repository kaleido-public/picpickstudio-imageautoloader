#include "capture_winrt.hpp"
using winrt::check_hresult;

GraphicsCaptureItem CaptureWinRT::getGraphicsCaptureItem(HWND window) {
    GraphicsCaptureItem item(nullptr);
    auto activation_factory = winrt::get_activation_factory<GraphicsCaptureItem>();
    auto interop_factory = activation_factory.as<IGraphicsCaptureItemInterop>();
    check_hresult(interop_factory->CreateForWindow(
        window,
        winrt::guid_of<IGraphicsCaptureItem>(),
        reinterpret_cast<void**>(winrt::put_abi(item)) /*output*/
    ));
    return item;
}

Direct3D11CaptureFramePool CaptureWinRT::getDirect3D11CaptureFramePool(GraphicsCaptureItem& item) {
    /* See winrt::com_ptr
       https://docs.microsoft.com/en-us/windows/uwp/cpp-and-winrt-apis/consume-com
    */
    winrt::com_ptr<ID3D11Device> d3d_device;
    /* See D3D11CreateDevice
       https://docs.microsoft.com/en-us/windows/win32/api/d3d11/nf-d3d11-d3d11createdevice
    */
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
        NULL
    ));

    auto idxgDevice = d3d_device.as<IDXGIDevice>();
    /* See IInspectable
       https://docs.microsoft.com/en-us/windows/uwp/cpp-and-winrt-apis/boxing
       https://docs.microsoft.com/en-us/windows/uwp/cpp-and-winrt-apis/consume-com
       https://docs.microsoft.com/en-us/windows/win32/com/com-technical-overview
    */
    winrt::com_ptr<::IInspectable> inspectable;
    check_hresult(CreateDirect3D11DeviceFromDXGIDevice(idxgDevice.get(), inspectable.put() /* output */));
    const IDirect3DDevice device = inspectable.as<IDirect3DDevice>();
    Direct3D11CaptureFramePool framePool = Direct3D11CaptureFramePool::Create(
        device,
        DirectXPixelFormat::B8G8R8A8UIntNormalized,
        1,          // capture 1 frame
        item.Size() // size of buffer
    );
    return framePool;
}

GraphicsCaptureSession CaptureWinRT::getGraphicsCaptureSession(GraphicsCaptureItem& item, Direct3D11CaptureFramePool& framePool) {
    GraphicsCaptureSession session = framePool.CreateCaptureSession(item);
    session.IsCursorCaptureEnabled(false);
    return session;
}

CaptureWindowOutput CaptureWinRT::getCapture(GraphicsCaptureItem& item, Direct3D11CaptureFramePool& framePool, GraphicsCaptureSession& session) {
    std::vector<byte> buffer{};
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
            bitmap.Close();
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

    CaptureWindowOutput output;
    output.size = size;
    output.frame = buffer;

    return output;

}

CaptureWindowOutput CaptureWinRT::startCapture(HWND window) {
    auto item = CaptureWinRT::getGraphicsCaptureItem(window);
    auto pool = CaptureWinRT::getDirect3D11CaptureFramePool(item);
    auto session = CaptureWinRT::getGraphicsCaptureSession(item, pool);
    auto output = CaptureWinRT::getCapture(item, pool, session);
    session.Close();
    pool.Close();
    return output;
}

CaptureWinRT CaptureWinRT::instance = CaptureWinRT();
