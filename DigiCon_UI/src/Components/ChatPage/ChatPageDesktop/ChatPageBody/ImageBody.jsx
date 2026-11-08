import React from "react";
// import image from "../../../../assets/background.png";
import image1 from "../../../../assets/homeDigi.png";
import image2 from "../../../../assets/DevOps/Pov.png";
import image3 from "../../../../assets/DevOps/Qode.png";
import image4 from "../../../../assets/DevOps/engagementModel.png";
import image5 from "../../../../assets/DevOps/PeopleArch.png";
import image6 from "../../../../assets/DevOps/BizDevOps.png";

import Carousel from "react-bootstrap/Carousel";
import { makeStyles } from "@material-ui/core/styles";
const useStyles = makeStyles(() => ({
  root: {
    marginTop: 10,
  },
}));

const ImageBody = () => {
  const classes = useStyles();
  return (
    <Carousel className={classes.root}>
      <Carousel.Item interval={1000}>
        <img className="d-block w-100" src={image1} alt="DigiCon" />
        {/* <Carousel.Caption>
          <h3>First slide label</h3>
          <p>Nulla vitae elit libero, a pharetra augue mollis interdum.</p>
        </Carousel.Caption> */}
      </Carousel.Item>
      <Carousel.Item interval={500}>
        <img className="d-block w-100" src={image2} alt="Pov" />
      </Carousel.Item>
      <Carousel.Item>
        <img className="d-block w-100" src={image3} alt="Qude" />
      </Carousel.Item>

      <Carousel.Item>
        <img className="d-block w-100" src={image4} alt="engagement model" />
      </Carousel.Item>
      <Carousel.Item>
        <img className="d-block w-100" src={image5} alt="People Architecture" />
      </Carousel.Item>
      <Carousel.Item>
        <img className="d-block w-100" src={image6} alt="BizDevOps" />
      </Carousel.Item>
    </Carousel>
  );
};

export default ImageBody;
