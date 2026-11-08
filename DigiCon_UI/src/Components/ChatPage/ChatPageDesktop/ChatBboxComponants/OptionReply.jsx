import React from "react";
// import Button from "@material-ui/core/Button";
import "../ChatBox.css";
import { makeStyles } from "@material-ui/core/styles";
import { animations } from "react-animation";
import Chip from "@material-ui/core/Chip";
const useStyles = makeStyles((theme) => ({
  root: {
    // background: "linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)",
    // backgroundImage: "linear-gradient(to right, #8E54E9 0%,  #FE6B8B  100%)",

    borderRadius: 10,
    border: 0,
    color: "#000",
    height: 48,
    padding: "0 30px",
    // boxShadow: "0 3px 5px 2px rgba(255, 105, 135, .3)",
    boxShadow:
      " 0 2.8px 2.2px rgba(0, 0, 0, 0.034), 0 6.7px 5.3px rgba(0, 0, 0, 0.048), 0 12.5px 10px rgba(0, 0, 0, 0.06), 0 22.3px 17.9px rgba(0, 0, 0, 0.072), 0 41.8px 33.4px rgba(0, 0, 0, 0.086), 0 100px 80px rgba(0, 0, 0, 0.12)",
    marginBottom: 10,
    "&:hover": {
      //   backgroundPosition: "right-center",
      background: "linear-gradient(to right, #4776E6 0%, #8E54E9  100%)",

      //   background: "#FE6B8B",
      //   boxShadow: "none",
      color: "#fff",
      textDecoration: "none",
    },
  },
  rootChip: {
    color: "#fff",
    fontSize: 13,
    background: "linear-gradient(to right, #868f96    0%, #596164  100%)",
    fontWeight: "bold",
    // backgroundColor: "##b19cd9 ",
  },
  label: {
    textTransform: "capitalize",
    fontSize: 12,
  },
  chips: {
    display: "flex",
    justifyContent: "center",
    flexWrap: "wrap",
    "& > *": {
      margin: theme.spacing(0.5),
    },
    marginBottom: 10,
  },
}));
const OptionReply = (props) => {
  const classes = useStyles();
  const chipsData = props.text.split(",");
  const chips = chipsData.map((i, index) => {
    return (
      <Chip
        label={i}
        key={index}
        classes={{
          root: classes.rootChip,
          label: classes.label,
        }}
      />
    );
  });

  return (
    <div className={classes.chips} style={{ animation: animations.popIn }}>
      {chips}
    </div>
  );
};

// const OptionReply = (props) => {
//   const classes = useStyles();
//   return (
//     <div
//       key={props.index}
//       className="responseContainerOption"
//       style={{ animation: animations.popIn }}
//     >
//       <Button
//         size="small"
//         variant="contained"
//         // color="primary"
//         classes={{
//           root: classes.root,
//           label: classes.label,
//         }}
//         onClick={() => props.onClickOptionEvent(props.text)}
//       >
//         {props.text}
//       </Button>
//     </div>
//   );
// };

export default OptionReply;
