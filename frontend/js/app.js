function showScreen(screenName) {

    document
        .querySelectorAll(".screen")
        .forEach(screen => {

            screen.classList.remove(
                "active"
            );

        });

    document
        .getElementById(
            `screen-${screenName}`
        )
        .classList.add("active");

}

function showToast(message) {

    const toast =
        document.getElementById(
            "toast"
        );

    const msg =
        document.getElementById(
            "toast-msg"
        );

    msg.textContent = message;

    toast.classList.add("show");

    setTimeout(() => {

        toast.classList.remove(
            "show"
        );

    }, 3000);
}

window.onload = async () => {

    try {

        const health =
            await getHealth();

        console.log(
            "Backend Connected",
            health
        );

    }
    catch(error){

        console.error(error);

    }

};