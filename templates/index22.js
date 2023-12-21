const downArrow = '🢓';
const upArrow = '🢑';
const dropdownLabelPlaceHolder =  "Select Months";
const dropdownLabelTextEl = document.getElementById("dropdown-label-text");
const checkboxes = document.querySelectorAll("input[type=checkbox][name=month]");
let selectedMonths = [];
let selcetedFile;
let selectedTags = "";
dropdownLabelTextEl.innerText = dropdownLabelPlaceHolder;

function onGenerateRevenue() {
    
    const fileInput = document.getElementById('upload');
    /*try{
        if(selectedTags == "" || !fileInput.file[0]){
            console.log(selectedTags, fileInput.file[0], 'data')
            return
        }
    }catch(e) {
        console.log(e)
        return

    }*/
   

    // for (var key of formData.entries()) {
    //      console.log(key[0] + ', ' + key[1]);
    // }
    var formdata = new FormData();
    formdata.append("months", selectedTags);
    formdata.append("file", fileInput.files[0]);

    var requestOptions = {
      method: 'POST',
      body: formdata,
      redirect: 'follow'
    };
    

    fetch("/process", requestOptions)
        .then(response => {
            if (response.status === 200) {
                alert("Click on ok to download the file")
                return response.blob();
            } else {
                //throw new Error(`HTTP status ${response.status}`);
                //const errorMessage = `${response.status}`;
                //window.location.href = 'error.html?message=' + encodeURIComponent(errorMessage);
                //alert(response);
                //throw new Error(errorMessage);
                return response.text().then(errorMessage => {
                    // Display the error message in an alert
                    alert(errorMessage);
                    throw new Error(errorMessage);
                });
            }
        })
        .then(result => {
            var contentType = 'application/vnd.ms-excel';
            var downloadLink = window.document.createElement('a');
            downloadLink.href = window.URL.createObjectURL(new Blob([result], { type: contentType }));
            downloadLink.download = 'Result.xlsx';
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            console.log(result);
        })
        .catch(error => {
            console.log('Error:', error);
            // Handle the error here, e.g., display a message to the user.
            //window.location.href = "templates/error.html";
            //window.location.href = `templates/error.html?message=${encodeURIComponent(errorMessage)}`;
        });
}

function onMonthDropdown() {
    const dropdownIcon = document.getElementById('dropdown-icon');
    const dropdownList =  document.getElementById("dropdown-value");
    dropdownList.classList.toggle("show");
    const isDropdownVisible = dropdownList.classList.contains("show");
    
    if(!isDropdownVisible) {
        dropdownList.style.display = "none"
        dropdownIcon.innerText = downArrow;
        dropdownIcon.style['margin-top'] = '16px'
    } else {
        dropdownList.style.display = "block";
        dropdownIcon.innerText = upArrow;
        dropdownIcon.style['margin-top'] = '-32px'
    }
    
}

window.addEventListener('click', function(e){   
    if (document.getElementById("dropdown-label").contains(e.target)){
        // Clicked in box
        onMonthDropdown()
    } else{
        if(document.getElementById("dropdown-value").contains(e.target)) return;
        const dropdownIcon = document.getElementById('dropdown-icon');
        const dropdownList =  document.getElementById("dropdown-value");
        const isDropdownVisible = dropdownList.classList.contains("show");
        if(isDropdownVisible){
            dropdownList.style.display = "none"
            dropdownIcon.innerText = downArrow;
            dropdownIcon.style['margin-top'] = '16px'
            dropdownList.classList.toggle("show");
        }
        // Clicked outside the box

    }
});

checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
        selectedMonths = Array.from(checkboxes) .filter((i) => i.checked).map((i) => i.value);

        selectedTags = "";
        selectedMonths.forEach((month, index) => {
            selectedTags +=  (index == selectedMonths.length - 1) ? month : month + ", ";
        });
        
        dropdownLabelTextEl.innerText = selectedTags || dropdownLabelPlaceHolder;
    });
});
