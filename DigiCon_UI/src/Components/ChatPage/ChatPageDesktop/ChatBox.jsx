import React, { Component } from "react";
import "./ChatBox.css";
import chatImage from "../../../assets/chat_icon.png";
import { Redirect } from "react-router-dom";
import ClearIcon from "@material-ui/icons/Clear";
import MinimizeIcon from "@material-ui/icons/Minimize";
import SendIcon from "@material-ui/icons/Send";
import { animations } from "react-animation";
import Typing from "../../UI/Typing/Typing";
import icon from "../../../assets/bot.png";
import Avtar from "./Avtar";

class ChatBox extends Component {
  messagesEndRef = React.createRef(null);

  constructor(props) {
    super(props);

    this.state = {
      loggedIn: true,
      min: false,
      connection: false,
      animation: [
        { animation: animations.bounceIn },
        { animation: animations.bounceOut },
      ],
    };
  }

  componentDidMount() {
    const token = localStorage.getItem("token");

    if (token == null) {
      this.setState({
        loggedIn: false,
      });
    }

    this.props.rasaConnect();
    this.props.ansibleConnect();

    setTimeout(() => {
      this.onButtonClick();
    }, 5000);
  }

  componentDidUpdate() {
    if (this.props.show === true) {
      this.scrollToBottom();

      if (this.inputField) {
        this.inputField.focus();
      }
    }
  }

  scrollToBottom = () => {
    if (this.messagesEndRef.current) {
      this.messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
      });
    }
  };

  onButtonClick = () => {
    if (this.props.show !== true) {
      this.props.setChatBoxShow(true, null);
      this.props.setChatBoxShow(true, 0);

      if (this.state.min !== true) {
        const message = {
          message: "start",
        };

        this.props.rasaEmit(message);
      }
    }
  };

  onMinimizeClick = () => {
    this.props.setChatBoxShow(false, 1);

    setTimeout(() => {
      this.props.setChatBoxShow(false, null);
      this.props.setTypingvalue(false);

      this.setState({
        min: true,
      });
    }, 200);
  };

  onCrossClick = () => {
    this.props.setChatBoxShow(false, 1);

    setTimeout(() => {
      this.props.setChatBoxShow(false, null);
      this.props.setTypingvalue(false);

      this.setState({
        min: false,
      });

      this.props.resetChat();
    }, 200);
  };

  onKeyPressEvent = (event) => {
    const code = event.keyCode || event.which;

    if (code === 13) {
      event.preventDefault();
      this.props.onSendMessgae(event);
    }
  };

  submitHandler = (event) => {
    event.preventDefault();
  };

  render() {
    if (this.state.loggedIn === false) {
      return <Redirect to="/login" />;
    }

    let UI = (
      <div
        id="chaticon"
        className="chatButton"
        onClick={this.onButtonClick}
      >
        <img
          className="chatIcon"
          alt="chatIcon"
          src={chatImage}
        />
      </div>
    );

    if (this.props.show === true) {
      UI = (
        <div
          id="chatwindow"
          className="chatBox"
          style={this.state.animation[this.props.anyIndex]}
        >
          <div className="chatBoxTop">
            <div className="headPart">
              <Avtar icon={icon} />
            </div>

            <div className="closeIcon">
              <ClearIcon onClick={this.onCrossClick} />
            </div>

            <div className="minimizeIcon">
              <MinimizeIcon onClick={this.onMinimizeClick} />
            </div>

            <div className="titleTop">
              DigiCon
            </div>
          </div>

          <div className="msgContainer">
            {this.props.chatValue}

            <div ref={this.messagesEndRef} />

            {this.props.typing === true ? <Typing /> : ""}
          </div>

          <div
            style={{
              padding: "6px 15px",
              display: "flex",
              alignItems: "center",
              backgroundColor: "#f7f7f7",
              borderTop: "1px solid #eeeeee",
            }}
          >
            <input
              type="checkbox"
              id="knowledgeGraph"
              checked={this.props.useKnowledgeGraph}
              onChange={this.props.onKnowledgeGraphChange}
            />

            <label
              htmlFor="knowledgeGraph"
              style={{
                marginLeft: "8px",
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              Ask Knowledge Graph
            </label>
          </div>

          <form
            id="form-reset"
            className="textbox"
            onSubmit={this.submitHandler}
          >
            <input
              type="text"
              className="inputfield"
              placeholder="Type a Message....."
              onChange={this.props.onChangeValue}
              onKeyPress={this.onKeyPressEvent}
              ref={(input) => {
                this.inputField = input;
              }}
            />

            <div
              className="sendButton"
              onClick={this.props.onSendMessgae}
            >
              <SendIcon />
            </div>
          </form>
        </div>
      );
    }

    return <React.Fragment>{UI}</React.Fragment>;
  }
}

export default ChatBox;