import React from "react";
import "../ChatBox.css";
import { animations } from "react-animation";
import bot from "../../../../assets/bot.png";
import Avtar from "./AvtarChat";

const BotReply = (props) => {
  return (
    <div
      key={props.index}
      className="responseContainer"
      style={{ animation: animations.popIn }}
    >
      <Avtar icon={bot} />

      <div className="replyBot">
        <p style={{ whiteSpace: "pre-wrap" }}>
          {props.text}
        </p>

        {props.diagram && (
          <div style={{ marginTop: "15px" }}>
            <img
              src={props.diagram}
              alt="Generated Diagram"
              style={{
                maxWidth: "100%",
                height: "auto",
                border: "1px solid #ddd",
                borderRadius: "8px",
                cursor: "pointer",
              }}
              onClick={() => window.open(props.diagram, "_blank")}
            />
          </div>
        )}

        {props.reportUrl && (
          <div style={{ marginTop: "15px" }}>
            <a
              href={props.reportUrl}
              target="_blank"
              rel="noopener noreferrer"
              download
              style={{
                display: "inline-block",
                padding: "10px 16px",
                background: "#1B2A4A",
                color: "#fff",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: 600,
              }}
            >
              Download SRE report
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default BotReply;