document.addEventListener('DOMContentLoaded', function(){

    var navbuttons = document.querySelectorAll(".navoption");
    console.log(navbuttons);

    

    navbuttons.forEach(button => {
        button.addEventListener("click", function(){
           var active = document.querySelector(".active");
            active.className = "navoption";
            button.className += " active";
        });
    });
});