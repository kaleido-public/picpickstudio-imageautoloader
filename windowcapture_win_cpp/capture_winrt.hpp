#pragma once
#include "capture.hpp"
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
#include <windows.graphics.capture.h>
#include <windows.system.h>
#include <inspectable.h>
#include <dxgi.h>
#include <typeinfo>
#include <stdexcept>
#include <d3d11.h>
#include <iostream>
#include <vector>


using namespace winrt::Windows::Graphics::Capture;
using namespace winrt::Windows::Foundation;
using namespace winrt::Windows::Graphics::DirectX;
using namespace winrt::Windows::Graphics::DirectX::Direct3D11;
using namespace winrt::Windows::Graphics::Imaging;
using Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess;

class CaptureWinRT {
    static GraphicsCaptureItem getGraphicsCaptureItem(HWND window);
    static Direct3D11CaptureFramePool getDirect3D11CaptureFramePool(GraphicsCaptureItem& item);
    static GraphicsCaptureSession getGraphicsCaptureSession(GraphicsCaptureItem& item, Direct3D11CaptureFramePool& framePool);
    static CaptureWindowOutput getCapture(GraphicsCaptureItem& item, Direct3D11CaptureFramePool& framePool, GraphicsCaptureSession& session);

public:
    CaptureWindowOutput startCapture(HWND window);
    static CaptureWinRT instance;
};
