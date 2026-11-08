import React from "react";
import { Document, pdfjs } from "react-pdf/dist/esm/entry.webpack";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;
const PdfBody = () => {
  // const [numPages, setNumPages] = useState(null);
  // const [pageNumber, setPageNumber] = useState(1);
  // function onDocumentLoadSuccess({ numPages }) {
  //   setNumPages(numPages);
  // }

  return (
    <React.Fragment>
      <Document file="./digicon.pdf">
        {/* onLoadSuccess={onDocumentLoadSuccess} */}
        {/* <Page pageNumber={pageNumber} /> */}
      </Document>
      {/* <p>
        Page {pageNumber} of {numPages}
      </p> */}
    </React.Fragment>
  );
};

export default PdfBody;
