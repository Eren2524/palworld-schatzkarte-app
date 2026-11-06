import SwiftUI
import WebKit

@main
struct PalKarteApp: App {
    var body: some Scene {
        WindowGroup {
            WebView()
                .ignoresSafeArea()
                .background(Color(red: 0.06, green: 0.11, blue: 0.13))
                .preferredColorScheme(nil)
        }
    }
}

/// Speichert alles, was die Seite in localStorage ablegt, zusätzlich in einer Datei im App-Ordner.
/// So bleiben die Häkchen auch dann erhalten, wenn iOS den Web-Speicher leert.
final class Store {
    static let shared = Store()
    private let url: URL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("palkarte-store.json")
    private(set) var data: [String: String] = [:]
    init() {
        if let d = try? Data(contentsOf: url), let obj = try? JSONSerialization.jsonObject(with: d) as? [String: String] { data = obj }
    }
    func set(_ k: String, _ v: String?) {
        if let v = v { data[k] = v } else { data.removeValue(forKey: k) }
        if let d = try? JSONSerialization.data(withJSONObject: data) { try? d.write(to: url, options: .atomic) }
    }
    func clear() { data = [:]; try? FileManager.default.removeItem(at: url) }
    var json: String {
        let d = (try? JSONSerialization.data(withJSONObject: data)) ?? Data("{}".utf8)
        return String(data: d, encoding: .utf8) ?? "{}"
    }
}

/// Liefert die eingebaute Seite unter app://karte/ aus (feste Herkunft statt file://).
final class LocalScheme: NSObject, WKURLSchemeHandler {
    func webView(_ webView: WKWebView, start task: WKURLSchemeTask) {
        guard let file = Bundle.main.url(forResource: "index", withExtension: "html"),
              let body = try? Data(contentsOf: file) else {
            task.didFailWithError(NSError(domain: "PalKarte", code: 404)); return
        }
        let resp = HTTPURLResponse(url: task.request.url!, statusCode: 200, httpVersion: "HTTP/1.1",
                                   headerFields: ["Content-Type": "text/html; charset=utf-8", "Content-Length": "\(body.count)"])!
        task.didReceive(resp); task.didReceive(body); task.didFinish()
    }
    func webView(_ webView: WKWebView, stop task: WKURLSchemeTask) {}
}

final class Bridge: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
    /// Haptisches Feedback (Antippen, Abhaken, Plan erstellt)
    static func haptic(_ kind: String) {
        DispatchQueue.main.async {
            switch kind {
            case "success": UINotificationFeedbackGenerator().notificationOccurred(.success)
            case "medium": UIImpactFeedbackGenerator(style: .medium).impactOccurred()
            default: UIImpactFeedbackGenerator(style: .light).impactOccurred()
            }
        }
    }
    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        guard let b = m.body as? [String: Any], let op = b["op"] as? String else { return }
        switch op {
        case "set": if let k = b["k"] as? String { Store.shared.set(k, b["v"] as? String) }
        case "del": if let k = b["k"] as? String { Store.shared.set(k, nil) }
        case "clear": Store.shared.clear()
        case "haptic": Bridge.haptic(b["k"] as? String ?? "light")
        default: break
        }
    }
    // Externe Links (Quellen, Fotos) in Safari öffnen
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url, let s = u.scheme, s == "http" || s == "https" {
            UIApplication.shared.open(u); decisionHandler(.cancel); return
        }
        decisionHandler(.allow)
    }
}

struct WebView: UIViewRepresentable {
    let bridge = Bridge()
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.setURLSchemeHandler(LocalScheme(), forURLScheme: "app")
        let js = """
        (function(){
          var data = \(Store.shared.json);
          function post(o){ try { window.webkit.messageHandlers.store.postMessage(o); } catch(e) {} }
          var shim = {
            getItem: function(k){ k=String(k); return Object.prototype.hasOwnProperty.call(data,k) ? data[k] : null; },
            setItem: function(k,v){ k=String(k); v=String(v); data[k]=v; post({op:'set',k:k,v:v}); },
            removeItem: function(k){ k=String(k); delete data[k]; post({op:'del',k:k}); },
            clear: function(){ data={}; post({op:'clear'}); },
            key: function(i){ var ks=Object.keys(data); return i<ks.length ? ks[i] : null; },
            get length(){ return Object.keys(data).length; }
          };
          try { Object.defineProperty(window, 'localStorage', { value: shim, configurable: true }); } catch(e) {}
        })();
        """
        cfg.userContentController.addUserScript(WKUserScript(source: js, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        cfg.userContentController.add(bridge, name: "store")
        let wv = WKWebView(frame: .zero, configuration: cfg)
        wv.navigationDelegate = bridge
        wv.scrollView.contentInsetAdjustmentBehavior = .never
        wv.scrollView.bounces = false
        wv.scrollView.isScrollEnabled = false
        wv.allowsBackForwardNavigationGestures = false
        wv.allowsLinkPreview = false
        wv.isOpaque = false
        wv.backgroundColor = UIColor(red: 0.06, green: 0.11, blue: 0.13, alpha: 1)
        wv.load(URLRequest(url: URL(string: "app://karte/index.html")!))
        return wv
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}
