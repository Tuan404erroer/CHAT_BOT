/* ========================================================= */
/*  STREAMLIT COMPONENT PROTOCOL                             */
/* ========================================================= */
const StreamlitApi = {
    setComponentReady() {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:componentReady",
            apiVersion: 1
        }, "*");
    },
    setFrameHeight(h) {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setFrameHeight",
            height: h
        }, "*");
    },
    setComponentValue(val) {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: val,
            dataType: "json"
        }, "*");
    }
};
