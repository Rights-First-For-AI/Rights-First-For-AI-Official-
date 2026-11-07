import { App } from "@modelcontextprotocol/ext-apps";
if (window.parent && window.parent !== window && typeof window.parent.postMessage === "function") {
  const app = new App({name:"TSPAI PLUS1",version:"0.3.0-pre.4-ui.1"}, {}, {autoResize:true});
  const bridge = {app, connected:false};
  window.tspaiMcpBridge = bridge;
  app.ontoolresult = result => {
    window.tspaiMcpToolResult = result;
    window.dispatchEvent(new CustomEvent("tspai:tool-result",{detail:result}));
  };
  window.tspaiMcpReady = app.connect(undefined,{timeout:12000}).then(() => {
    bridge.connected = true;
  });
}