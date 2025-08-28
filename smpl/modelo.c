/* ----------------------------------------------------------------------- 
C�digo gerado com o ASDA - Ambiente de Simula��o Distribu�da Autom�tico
--------------------------------------------------------------------------*/
#include "smpl.h"

main()
{
 /* definicoes */
 float Te = 100000;
 int Event = 1, Customer = 1, Aleatorio;
 float Ta1 = 0.0833, Ts1 = 0.04, Ts2 = 0.05;
 int i = 0;

 char flag_reset = 0;
 float timeWarmUp = 5000.0;
 int CS_1, CS_2;
 FILE *p, *saida;
 saida = fopen("untitled.out","w");

 if ((p = sendto(saida)) == NULL)
    printf("Erro na saida \n");


 /* prepara o sistema de simulacao e da nome ao modelo */
 smpl(0," MREL2");


 /* cria e da nome as facilidades */
 CS_1 = facility("CS_1",1);
 CS_2 = facility("CS_2",1);

 /* escalona a chegada do primeiro cliente */
   schedule(1,0.0, Customer);



 while ( (time() < Te) )
{
   if ( (!flag_reset) && (time() > timeWarmUp) )
   {
      reset();
      flag_reset = 1;
   }
    cause(&Event,&Customer);
    switch(Event)
    {
        case 1 : 
          schedule(2,0.0, Customer);
          schedule(1,expntl(Ta1), Customer);
          break;

        /*  centro de servio = CS_1 */
        case 2 : 
          if (request(CS_1, Customer,0) == 0)
             schedule(3,expntl(Ts1), Customer);
          break;
        case 3 : 
          release(CS_1, Customer);
          Aleatorio = randomX(1,10000);
          if (( 1 <= Aleatorio) && ( Aleatorio <= 2000) )
           schedule(4,0.0, Customer);
          break;

        /*  centro de servio = CS_2 */
        case 4 : 
          if (request(CS_2, Customer,0) == 0)
             schedule(5,expntl(Ts2), Customer);
          break;
        case 5 : 
          release(CS_2, Customer);
             schedule(2,0.0, Customer);
          break;
 }
}


/* gera o relatorio da simulacao */
   report();
   fclose(saida);
}
/* ----------------------------------------------------------------------- */
