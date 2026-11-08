import React, { Component } from "react";
import "./ChatBox.css";
import chatImage from "../../../assets/chat_icon.png";
import { Redirect } from "react-router-dom";
import ClearIcon from "@material-ui/icons/Clear";
import MinimizeIcon from "@material-ui/icons/Minimize";
import SendIcon from "@material-ui/icons/Send";
import axios from "axios";
import apiUrl from "../../../Service/api";
import { animations } from "react-animation";
// import { easings } from "react-animation";
import Typing from "../Typing/Typing";
class ChatBox extends Component {
  messagesEndRef = React.createRef(null);
  constructor(props) {
    super(props);

    this.state = {
      // messagesEnd: React.createRef(),
      loggedIn: true,
      show: false,
      msg: "",
      min: false,
      anyIndex: 0,
      typing: false,
      animation: [
        { animation: animations.bounceIn },
        { animation: animations.bounceOut },
      ],
      chat: [],
    };
  }
  scrollToBottom = () => {
    this.messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };
  componentDidMount() {
    const token = localStorage.getItem("token");
    if (token == null) {
      this.setState({
        loggedIn: false,
      });
    }
  }
  componentDidUpdate() {
    if (this.state.show === true) {
      this.scrollToBottom();
      this.inputField.focus();
    }
  }

  onButtonClick = () => {
    this.setState({
      anyIndex: 0,
      show: true,
    });
    if (this.state.min === false) {
      setTimeout(() => {
        this.setState({
          chat: [
            {
              type: "bot",
              Message: "Hi I am DigiCon Bot",
            },
          ],
        });
      }, 1200);
    }

    console.log(this.state.show);
  };
  onMinimizeClick = () => {
    this.setState({
      anyIndex: 1,
    });
    setTimeout(() => {
      this.setState({
        show: false,
        min: true,
      });
    }, 200);

    console.log(this.state.show);
  };

  onCrossClick = () => {
    this.setState({
      anyIndex: 1,
    });
    setTimeout(() => {
      this.setState({
        show: false,
        min: false,
        chat: [],
      });
    }, 200);
    console.log(this.state.show);
  };
  onChangeValue = (e) => {
    this.setState({
      msg: e.target.value,
    });
  };

  onSendMessgae = (e) => {
    if (this.state.msg !== "") {
      const message = {
        message: this.state.msg,
      };
      const chat = [
        ...this.state.chat,
        {
          type: "user",
          Message: this.state.msg,
        },
      ];
      this.setState({ chat, msg: "", typing: true });
      console.log(`------> ${apiUrl.chatApi}`);
      axios
        .post(apiUrl.chatApi, message)
        .then((response) => {
          console.log(response.data);
          const chat = [
            ...this.state.chat,

            {
              type: "bot",
              Message: response.data.response,
            },
          ];
          this.setState({ chat, typing: false });
          // if (response.data.response === "Video is streaming...")
          if (response.data.response === "")
            setTimeout(() => {
              this.onMinimizeClick();
              this.props.setBody();
            }, 2000);
        })
        .catch((err) => {
          console.log(err);
          const chat = [
            ...this.state.chat,

            {
              type: "bot",
              Message: `Network Error caused by ${err}`,
            },
          ];
          this.setState({ chat, typing: false });
          // this.props.setBody();
        });
    }

    document.getElementById("form-reset").reset();
  };

  onKeyPressEvent = (event) => {
    var code = event.keyCode || event.which;
    if (code === 13) {
      this.onSendMessgae(event);
    }

    // event.preventDefault();
  };
  submitHandler(e) {
    e.preventDefault();
  }
  render() {
    if (this.state.loggedIn === false) {
      return <Redirect to="/login" />;
    }
    let chat = this.state.chat.map((i, index) => {
      if (i.type === "bot") {
        return (
          <div
            key={index}
            className="responseContainer"
            style={{ animation: animations.popIn }}
          >
            <div className="replyBot">
              <p>{i.Message}</p>
            </div>
          </div>
        );
      } else {
        return (
          <div
            key={index}
            className="userContainer"
            style={{ animation: animations.popIn }}
          >
            <div className="chatUser">
              <p>{i.Message}</p>
            </div>
          </div>
        );
      }
    });
    let UI = (
      <div id="chaticon" className="chatButton" onClick={this.onButtonClick}>
        <img className="chatIcon" alt="chatIcon" src={chatImage}></img>
      </div>
    );
    if (this.state.show === true) {
      UI = (
        <div
          id="chatwindow"
          className="chatBox"
          style={this.state.animation[this.state.anyIndex]}
        >
          <div className="chatBoxTop">
            <div className="closeIcon">
              <ClearIcon onClick={this.onCrossClick} />
            </div>
            <div className="minimizeIcon">
              <MinimizeIcon onClick={this.onMinimizeClick} />
            </div>
            <div className="titleTop"> </div>
          </div>
          <div className="msgContainer">
            {chat} <div ref={this.messagesEndRef} />{" "}
            {this.state.typing === true ? <Typing /> : ""}
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
              onChange={this.onChangeValue}
              onKeyPress={this.onKeyPressEvent}
              ref={(input) => {
                this.inputField = input;
              }}
            ></input>
            <div className="sendButton" onClick={this.onSendMessgae}>
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
